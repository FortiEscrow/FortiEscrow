# Escrow Semantics

This document defines the formal semantics of the FortiEscrow state machine.

## State Machine Definition

### States

| State | Value | Description |
|-------|-------|-------------|
| INIT | 0 | Contract deployed, awaiting funding |
| FUNDED | 1 | Funds deposited, awaiting resolution |
| RELEASED | 2 | Funds transferred to beneficiary (terminal) |
| REFUNDED | 3 | Funds returned to depositor (terminal) |

### Transitions

```
         ┌─────────────────────────────────────────────────────────┐
         │                                                         │
         │    INIT ──────[fund]──────> FUNDED                     │
         │                               │                         │
         │                               ├──[release]──> RELEASED  │
         │                               │                         │
         │                               └──[refund]───> REFUNDED  │
         │                               │                         │
         │                               └──[force_refund]──────┘  │
         │                                   (after timeout)       │
         │                                                         │
         └─────────────────────────────────────────────────────────┘
```

| Transition | From | To | Authorization | Condition |
|------------|------|----|--------------:|-----------|
| fund | INIT | FUNDED | depositor | amount == escrow_amount |
| release | FUNDED | RELEASED | depositor | now <= deadline |
| refund | FUNDED | REFUNDED | depositor | - |
| force_refund | FUNDED | REFUNDED | anyone | now > deadline |

### Terminal States

RELEASED and REFUNDED are terminal states. No transitions are possible from terminal states. This property is enforced by requiring `state == FUNDED` for all resolution operations.

## Storage Schema

```
depositor        : address    # Funds the escrow, controls release/refund
beneficiary      : address    # Receives funds on release
escrow_amount    : nat        # Required funding amount (mutez)
timeout_seconds  : nat        # Duration before force_refund available
state            : int        # Current FSM state (0-3)
funded_at        : timestamp  # Time when fund() was called
deadline         : timestamp  # funded_at + timeout_seconds
```

### Immutability

All fields except `state`, `funded_at`, and `deadline` are immutable after deployment. `funded_at` and `deadline` are set exactly once when `fund()` is called.

## Security Invariants

FortiEscrow enforces five security invariants. These are not optional guidelines; they are runtime-enforced constraints.

### Invariant 1: Funds Safety

**Statement**: Funds can only be transferred when the contract reaches a terminal state.

```
∀t: transfer(amount) → state(t) ∈ {RELEASED, REFUNDED}
```

**Enforcement**: All `sp.send()` calls occur only in `release()`, `refund()`, and `force_refund()`, each of which first transitions state to terminal before transferring.

### Invariant 2: State Consistency

**Statement**: State transitions follow the FSM definition exactly. No backward transitions are possible.

```
INIT → FUNDED → {RELEASED | REFUNDED}
```

**Enforcement**: Every entrypoint verifies the current state before modifying it. Terminal states have no outgoing transitions.

### Invariant 3: Authorization Correctness

**Statement**: Only authorized parties can execute privileged operations.

| Operation | Authorized Caller |
|-----------|-------------------|
| fund | depositor |
| release | depositor |
| refund | depositor |
| force_refund | anyone (after timeout) |

**Enforcement**: `sp.verify(sp.sender == depositor)` on all privileged operations.

### Invariant 4: Time Safety

**Statement**: Funds are always recoverable after the deadline expires.

```
∀t ≥ deadline: force_refund() succeeds
```

**Enforcement**:
- Deadline is calculated at funding time: `deadline = now + timeout_seconds`
- Deadline is immutable after funding
- Timeout bounds enforced: 1 hour ≤ timeout ≤ 1 year

### Invariant 5: No Permanent Fund-Locking

**Statement**: There exists no execution path that results in funds being permanently locked.

**Exit paths from FUNDED state**:
1. `release()` → depositor transfers to beneficiary (anytime before deadline)
2. `refund()` → depositor reclaims funds (anytime)
3. `force_refund()` → anyone recovers funds (after deadline)

**Enforcement**: Multiple independent exit paths ensure funds are always recoverable.

## Validation Rules

### Initialization Validation

| Check | Error Code | Rationale |
|-------|------------|-----------|
| depositor != beneficiary | SAME_PARTY | Prevents self-escrow exploit |
| amount > 0 | ZERO_AMOUNT | Prevents empty escrows |
| timeout >= 3600 | TIMEOUT_TOO_SHORT | Minimum 1 hour dispute window |
| timeout <= 31536000 | TIMEOUT_TOO_LONG | Maximum 1 year (sanity bound) |

### Fund Validation

| Check | Error Code |
|-------|------------|
| state == INIT | ALREADY_FUNDED |
| sender == depositor | NOT_DEPOSITOR |
| amount == escrow_amount | AMOUNT_MISMATCH |

### Release Validation

| Check | Error Code |
|-------|------------|
| state == FUNDED | NOT_FUNDED |
| sender == depositor | NOT_DEPOSITOR |
| now <= deadline | DEADLINE_PASSED |

### Refund Validation

| Check | Error Code |
|-------|------------|
| state == FUNDED | NOT_FUNDED |
| sender == depositor | NOT_DEPOSITOR |

### Force Refund Validation

| Check | Error Code |
|-------|------------|
| state == FUNDED | NOT_FUNDED |
| now > deadline | TIMEOUT_NOT_EXPIRED |

## Execution Semantics

### Checks-Effects-Interactions Pattern

All entrypoints follow this order:

1. **Checks**: Validate state, authorization, and parameters
2. **Effects**: Update contract state
3. **Interactions**: Execute external calls (transfers)

This ordering prevents reentrancy attacks by ensuring state is terminal before any external call.

### Exact Amount Matching

Funding requires exact amount matching (`sp.amount == escrow_amount`). This prevents:
- Underfunding (partial deposits)
- Overfunding (excess funds locked)

### Direct Transfer Rejection

The `default` entrypoint rejects all direct XTZ transfers. Funds can only enter through `fund()`, ensuring the state machine tracks all deposits.

## Formal Properties

### Monotonicity

State values are monotonically increasing: INIT(0) < FUNDED(1) < RELEASED(2), REFUNDED(3).

### Determinism

For any given contract state and valid input, the resulting state is deterministic.

### Finality

Once a terminal state is reached, the contract state is immutable. All funds have been disbursed.

### Liveness

Given any FUNDED escrow, at least one of the following will eventually succeed:
- depositor calls `release()` or `refund()`
- deadline passes and anyone calls `force_refund()`
