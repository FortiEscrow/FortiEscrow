# Escrow Semantics

This document defines the formal semantics of the FortiEscrow state machine for both SimpleEscrow and MultiSigEscrow contracts.

## State Machine Definition

### States

| State | Value | Description |
|-------|-------|-------------|
| INIT | 0 | Contract deployed, awaiting funding |
| FUNDED | 1 | Funds deposited, awaiting resolution |
| RELEASED | 2 | Funds transferred to beneficiary (terminal) |
| REFUNDED | 3 | Funds returned to depositor (terminal) |

### SimpleEscrow Transitions

```
         ┌─────────────────────────────────────────────────────────┐
         │                                                         │
         │    INIT ──────[fund]──────> FUNDED                     │
         │                               │                         │
         │                               ├──[release]──> RELEASED  │
         │                               │                         │
         │                               ├──[refund]───> REFUNDED  │
         │                               │                         │
         │                               └──[force_refund]──────┘  │
         │                                   (at or after timeout) │
         │                                                         │
         └─────────────────────────────────────────────────────────┘
```

| Transition | From | To | Authorization | Condition |
|------------|------|----|--------------:|-----------|
| fund | INIT | FUNDED | depositor | amount == escrow_amount |
| release | FUNDED | RELEASED | depositor | now < deadline |
| refund | FUNDED | REFUNDED | depositor | - |
| force_refund | FUNDED | REFUNDED | anyone | now >= deadline |

### MultiSigEscrow Transitions

```
         ┌──────────────────────────────────────────────────────────────┐
         │                                                              │
         │    INIT ──────[fund]──────> FUNDED                          │
         │                               │                              │
         │                               ├──[vote_release x2]──> RELEASED │
         │                               │                              │
         │                               ├──[vote_refund x2]──> REFUNDED  │
         │                               │                              │
         │                               └──[force_refund]───────────┘  │
         │                                   (at or after timeout)      │
         │                                                              │
         └──────────────────────────────────────────────────────────────┘
```

| Transition | From | To | Authorization | Condition |
|------------|------|----|--------------:|-----------|
| fund | INIT | FUNDED | depositor | amount == escrow_amount |
| vote_release (consensus) | FUNDED | RELEASED | 2-of-3 parties | release_votes >= 2 |
| vote_refund (consensus) | FUNDED | REFUNDED | 2-of-3 parties | refund_votes >= 2 |
| force_refund | FUNDED | REFUNDED | anyone | now >= deadline |

### Terminal States

RELEASED and REFUNDED are terminal states. No transitions are possible from terminal states. This property is enforced by requiring `state == FUNDED` for all resolution operations.

## Storage Schema

### SimpleEscrow Storage

```
depositor        : address    # Funds the escrow, controls release/refund
beneficiary      : address    # Receives funds on release
escrow_amount    : nat        # Required funding amount (mutez)
timeout_seconds  : nat        # Duration before force_refund available
state            : int        # Current FSM state (0-3)
funded_at        : timestamp  # Time when fund() was called
deadline         : timestamp  # funded_at + timeout_seconds
```

### MultiSigEscrow Storage

```
depositor          : address    # Funds the escrow
beneficiary        : address    # Receives funds on release
arbiter            : address    # Neutral third party for dispute resolution
escrow_amount      : nat        # Required funding amount (mutez)
timeout_seconds    : nat        # Duration before force_refund available
state              : int        # Current FSM state (0-3)
funded_at          : timestamp  # Time when fund() was called
deadline           : timestamp  # funded_at + timeout_seconds

# Voting state
votes              : map(address -> int)  # Party -> VOTE_RELEASE(0) or VOTE_REFUND(1)
release_votes      : nat        # Count of release votes
refund_votes       : nat        # Count of refund votes
consensus_executed : bool       # Guard against double consensus execution
depositor_voted    : bool       # Per-voter lock: depositor has voted
beneficiary_voted  : bool       # Per-voter lock: beneficiary has voted
arbiter_voted      : bool       # Per-voter lock: arbiter has voted

# Dispute tracking
dispute_state      : int        # NONE(0), PENDING(1), RESOLVED(2)
dispute_reason     : string     # Reason for dispute
dispute_open_at    : timestamp  # When dispute was raised
dispute_deadline   : timestamp  # Arbiter must resolve by this time
dispute_resolver   : address    # Who resolved the dispute
dispute_outcome    : int        # RELEASE(0), REFUND(1), unresolved(-1)
```

### Immutability

**SimpleEscrow**: All fields except `state`, `funded_at`, and `deadline` are immutable after deployment. `funded_at` and `deadline` are set exactly once when `fund()` is called.

**MultiSigEscrow**: Party addresses, `escrow_amount`, and `timeout_seconds` are immutable. `funded_at` and `deadline` are set once at funding. Voting state and dispute fields are mutable during the FUNDED state and are reset on terminal state entry.

## MultiSig Voting Rules

### Consensus Mechanism

1. **2-of-3 Threshold**: Any two of the three parties (depositor, beneficiary, arbiter) must agree
2. **One Vote Per Party**: Each party can cast exactly one vote per escrow cycle (enforced by per-voter locks)
3. **No Vote Changes**: Once a party votes (release or refund), their position is locked
4. **Automatic Execution**: When the 2nd matching vote is cast, consensus executes immediately
5. **Mutual Exclusion**: Release and refund consensus cannot both be reached (maximum 3 votes total)

### Consensus Execution Guards

Before executing consensus, the contract verifies:

1. `consensus_executed == false` (prevents double settlement)
2. `state == FUNDED` (prevents invalid state transitions)
3. `~(release_votes >= 2 AND refund_votes >= 2)` (mutual exclusion assertion)
4. Voting invariant verification (manual recount matches counters)

### Voting State Lifecycle

| State | Voting State |
|-------|-------------|
| INIT | Empty (not yet relevant) |
| FUNDED | Active (voting in progress) |
| RELEASED | Reset (cleared on entry) |
| REFUNDED | Reset (cleared on entry) |

When entering a terminal state, `_reset_voting_state()` clears all voting data: the votes map, vote counters, per-voter locks, and the consensus_executed flag.

## Security Invariants

FortiEscrow enforces five security invariants. These are not optional guidelines; they are runtime-enforced constraints.

### Invariant 1: Funds Safety

**Statement**: Funds can only be transferred when the contract reaches a terminal state.

```
∀t: transfer(amount) → state(t) ∈ {RELEASED, REFUNDED}
```

**Enforcement**: All fund transfers route through `_settle(recipient)` which uses `sp.balance` (not `escrow_amount`). The caller changes state to terminal before calling `_settle()`, following the CEI pattern.

### Invariant 2: State Consistency

**Statement**: State transitions follow the FSM definition exactly. No backward transitions are possible.

```
INIT → FUNDED → {RELEASED | REFUNDED}
```

**Enforcement**: Every entrypoint verifies the current state before modifying it. Terminal states have no outgoing transitions.

### Invariant 3: Authorization Correctness

**Statement**: Only authorized parties can execute privileged operations.

**SimpleEscrow**:

| Operation | Authorized Caller |
|-----------|-------------------|
| fund | depositor |
| release | depositor |
| refund | depositor |
| force_refund | anyone (at or after timeout) |

**MultiSigEscrow**:

| Operation | Authorized Caller |
|-----------|-------------------|
| fund | depositor |
| vote_release | depositor, beneficiary, or arbiter |
| vote_refund | depositor, beneficiary, or arbiter |
| raise_dispute | depositor or beneficiary |
| force_refund | anyone (at or after timeout) |

**Enforcement**: `sp.verify(sp.sender == ...)` on all privileged operations.

### Invariant 4: Time Safety

**Statement**: Funds are always recoverable at or after the deadline.

```
∀t >= deadline: force_refund() succeeds (if state == FUNDED)
```

**Enforcement**:
- Deadline is calculated at funding time: `deadline = now + timeout_seconds`
- Deadline is immutable after funding
- Timeout bounds enforced: 1 hour <= timeout <= 1 year
- Recovery condition: `now >= deadline` (at-or-after, not strictly-after)

### Invariant 5: No Permanent Fund-Locking

**Statement**: There exists no execution path that results in funds being permanently locked.

**SimpleEscrow exit paths from FUNDED**:
1. `release()` — depositor transfers to beneficiary (before deadline)
2. `refund()` — depositor reclaims funds (anytime)
3. `force_refund()` — anyone recovers funds (at or after deadline)

**MultiSigEscrow exit paths from FUNDED**:
1. `vote_release()` — 2-of-3 consensus releases to beneficiary
2. `vote_refund()` — 2-of-3 consensus refunds to depositor
3. `force_refund()` — anyone recovers funds (at or after deadline)

**Enforcement**: Multiple independent exit paths ensure funds are always recoverable. Settlement uses `sp.balance` (not `escrow_amount`) to prevent residual fund lockup.

## Validation Rules

### Initialization Validation

| Check | Error Code | Rationale |
|-------|------------|-----------|
| depositor != beneficiary | SAME_PARTY | Prevents self-escrow exploit |
| amount > 0 | ZERO_AMOUNT | Prevents empty escrows |
| timeout >= 3600 | TIMEOUT_TOO_SHORT | Minimum 1 hour dispute window |
| timeout <= 31536000 | TIMEOUT_TOO_LONG | Maximum 1 year (sanity bound) |

MultiSigEscrow additionally requires:
| All three addresses different | SAME_PARTY | Prevents role overlap |

### Fund Validation

| Check | Error Code |
|-------|------------|
| state == INIT | ALREADY_FUNDED |
| sender == depositor | NOT_DEPOSITOR |
| amount == escrow_amount | AMOUNT_MISMATCH |

### Release Validation (SimpleEscrow)

| Check | Error Code |
|-------|------------|
| state == FUNDED | NOT_FUNDED |
| sender == depositor | NOT_DEPOSITOR |
| now < deadline | DEADLINE_PASSED |

### Force Refund Validation

| Check | Error Code |
|-------|------------|
| state == FUNDED | NOT_FUNDED |
| now >= deadline | TIMEOUT_NOT_EXPIRED |

### Vote Validation (MultiSigEscrow)

| Check | Error Code |
|-------|------------|
| state == FUNDED | NOT_FUNDED |
| consensus_executed == false | CONSENSUS_ALREADY_EXECUTED |
| sender is a party | UNAUTHORIZED |
| sender has not voted | *_ALREADY_VOTED |

## Execution Semantics

### Checks-Effects-Interactions Pattern

All entrypoints follow this order:

1. **Checks**: Validate state, authorization, and parameters
2. **Effects**: Update contract state (transition to terminal)
3. **Interactions**: Execute external calls (transfers via `_settle()`)

This ordering prevents reentrancy attacks by ensuring state is terminal before any external call.

### Centralized Settlement

Both SimpleEscrow and MultiSigEscrow use `_settle(recipient)` for all fund transfers:
- Uses `sp.balance` (not `escrow_amount`) to transfer ALL contract funds
- Prevents residual fund lockup from extra XTZ sent to the contract
- Single point of control for audit and security review

### Exact Amount Matching

Funding requires exact amount matching (`sp.amount == escrow_amount`). This prevents:
- Underfunding (partial deposits)
- Overfunding (excess funds locked)

### Direct Transfer Rejection

The `default` entrypoint (SimpleEscrow) rejects all direct XTZ transfers. Funds can only enter through `fund()`, ensuring the state machine tracks all deposits.

### Deadline Boundary Semantics

```
Timeline:      [fund_at] ←── timeout_seconds ──→ [deadline]

release window:       [fund_at, deadline)    ← strictly before deadline
force_refund window:              [deadline, ∞)  ← from deadline onward

At now == deadline:
  release():       now < deadline? NO  → FAILS
  force_refund():  now >= deadline? YES → SUCCEEDS
```

No gap, no overlap. The deadline is the exact, deterministic boundary.

## Formal Properties

### Monotonicity

State values are monotonically increasing: INIT(0) < FUNDED(1) < RELEASED(2), REFUNDED(3).

### Determinism

For any given contract state and valid input, the resulting state is deterministic.

### Finality

Once a terminal state is reached, the contract state is immutable. All funds have been disbursed.

### Liveness

Given any FUNDED escrow, at least one of the following will eventually succeed:

**SimpleEscrow**:
- depositor calls `release()` or `refund()`
- deadline passes and anyone calls `force_refund()`

**MultiSigEscrow**:
- 2-of-3 parties vote for release or refund
- deadline passes and anyone calls `force_refund()`

### Consensus Safety (MultiSigEscrow)

- No single party can unilaterally move funds
- Arbiter cannot access funds alone
- Each party votes exactly once (no vote manipulation)
- Consensus executes at most once per escrow cycle
- Voting invariants are verified before consensus execution
