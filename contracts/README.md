# Contracts

Smart contract implementations for the FortiEscrow framework.

## Structure

```
contracts/
├── core/
│   ├── escrow_base.py              # Base contract + SimpleEscrow
│   ├── escrow_multisig.py          # 2-of-3 multi-signature variant
│   ├── escrow_factory.py           # Factory deployment pattern
│   ├── invariants.py               # Formal invariant definitions
│   └── invariants_enforcement.py   # Runtime invariant checking
├── interfaces/
│   ├── types.py                    # Type definitions
│   ├── errors.py                   # Error codes
│   └── events.py                   # Event definitions
├── utils/
│   ├── validators.py               # Input validators
│   ├── amount_validator.py         # Amount validation
│   └── timeline_manager.py         # Timeout utilities
└── adapters/
    └── escrow_adapter.py           # Factory/registry adapter
```

## SimpleEscrow

**Location**: `core/escrow_base.py`

Two-party escrow where the depositor controls release and refund.

### Storage

| Field | Type | Description |
|-------|------|-------------|
| depositor | address | Funds escrow, controls release/refund |
| beneficiary | address | Receives funds on release |
| escrow_amount | nat | Required funding amount (mutez) |
| timeout_seconds | nat | Duration before force_refund available |
| state | int | FSM state: 0=INIT, 1=FUNDED, 2=RELEASED, 3=REFUNDED |
| funded_at | timestamp | Time when funded |
| deadline | timestamp | funded_at + timeout_seconds |

### State Machine

```
INIT ──[fund]──> FUNDED ──[release]──> RELEASED (terminal)
                    │
                    ├──[refund]──────> REFUNDED (terminal)
                    └──[force_refund]─> REFUNDED (at or after timeout)
```

### Entrypoints

| Entrypoint | Transition | Authorization | Condition |
|------------|------------|---------------|-----------|
| fund() | INIT -> FUNDED | depositor | amount == escrow_amount |
| release() | FUNDED -> RELEASED | depositor | now < deadline |
| refund() | FUNDED -> REFUNDED | depositor | - |
| force_refund() | FUNDED -> REFUNDED | anyone | now >= deadline |
| default() | - | - | Always fails (rejects direct transfers) |

### Views

| View | Returns |
|------|---------|
| get_status() | state, parties, amount, deadline, action flags |
| get_parties() | depositor, beneficiary |
| get_timeline() | funded_at, deadline, timeout_seconds, is_expired |

## MultiSigEscrow

**Location**: `core/escrow_multisig.py`

Three-party escrow with 2-of-3 consensus voting and arbiter dispute resolution.

### Storage

| Field | Type | Description |
|-------|------|-------------|
| depositor | address | Funds the escrow |
| beneficiary | address | Receives funds on release |
| arbiter | address | Neutral third party for disputes |
| escrow_amount | nat | Required funding amount (mutez) |
| timeout_seconds | nat | Duration before force_refund available |
| state | int | FSM state: 0=INIT, 1=FUNDED, 2=RELEASED, 3=REFUNDED |
| funded_at | timestamp | Time when funded |
| deadline | timestamp | funded_at + timeout_seconds |
| votes | map(address -> int) | Party vote records (0=RELEASE, 1=REFUND) |
| release_votes | nat | Count of release votes |
| refund_votes | nat | Count of refund votes |
| consensus_executed | bool | Guard against double consensus execution |
| depositor_voted | bool | Per-voter lock: depositor has voted |
| beneficiary_voted | bool | Per-voter lock: beneficiary has voted |
| arbiter_voted | bool | Per-voter lock: arbiter has voted |
| dispute_state | int | NONE(0), PENDING(1), RESOLVED(2) |
| dispute_reason | string | Reason for dispute |
| dispute_open_at | timestamp | When dispute was raised |
| dispute_deadline | timestamp | Arbiter must resolve by this time |
| dispute_resolver | address | Who resolved the dispute |
| dispute_outcome | int | RELEASE(0), REFUND(1), unresolved(-1) |

### State Machine

```
INIT ──[fund]──> FUNDED ──[vote_release x2]──> RELEASED (terminal)
                    │
                    ├──[vote_refund x2]──────> REFUNDED (terminal)
                    └──[force_refund]─────────> REFUNDED (at or after timeout)
```

### Entrypoints

| Entrypoint | Transition | Authorization | Condition |
|------------|------------|---------------|-----------|
| fund() | INIT -> FUNDED | depositor | amount == escrow_amount |
| vote_release() | FUNDED -> RELEASED (if consensus) | any party | not already voted |
| vote_refund() | FUNDED -> REFUNDED (if consensus) | any party | not already voted |
| raise_dispute(reason) | - (informational) | depositor/beneficiary | state == FUNDED |
| force_refund() | FUNDED -> REFUNDED | anyone | now >= deadline |

### Views

| View | Returns |
|------|---------|
| get_status() | state, parties, amount, deadline, vote counts, dispute state |
| get_votes() | per-party votes, vote counts, votes_needed |
| get_parties() | depositor, beneficiary, arbiter |

### Voting Rules

1. Each party can cast exactly one vote (no changes allowed)
2. 2-of-3 matching votes triggers automatic execution
3. Voting invariants verified before consensus execution
4. All voting state reset on terminal state entry

## Usage

### SimpleEscrow

```python
from contracts.core.escrow_base import SimpleEscrow
import smartpy as sp

escrow = SimpleEscrow(
    depositor=sp.address("tz1Alice..."),
    beneficiary=sp.address("tz1Bob..."),
    amount=sp.nat(5_000_000),
    timeout_seconds=sp.nat(604800)
)
```

### MultiSigEscrow

```python
from contracts.core.escrow_multisig import MultiSigEscrow
import smartpy as sp

escrow = MultiSigEscrow(
    depositor=sp.address("tz1Alice..."),
    beneficiary=sp.address("tz1Bob..."),
    arbiter=sp.address("tz1Charlie..."),
    amount=sp.nat(5_000_000),
    timeout_seconds=sp.nat(604800)
)
```

### Factory Deployment

```python
from contracts.core.escrow_factory import EscrowFactory

factory = EscrowFactory()
# Deploy multiple escrows with consistent configuration
```

## Error Codes

| Code | Description |
|------|-------------|
| ESCROW_INVALID_STATE | Invalid state for operation |
| ESCROW_NOT_DEPOSITOR | Sender is not depositor |
| ESCROW_AMOUNT_MISMATCH | Amount != escrow_amount |
| ESCROW_TIMEOUT_NOT_EXPIRED | Deadline not reached |
| ESCROW_DEADLINE_PASSED | Release window closed |
| ESCROW_SAME_PARTY | Party addresses are identical |
| ESCROW_ZERO_AMOUNT | amount == 0 |
| ESCROW_TIMEOUT_TOO_SHORT | timeout < 1 hour |
| ESCROW_TIMEOUT_TOO_LONG | timeout > 1 year |
| ESCROW_UNAUTHORIZED | Sender not authorized |
| ESCROW_DIRECT_TRANSFER_NOT_ALLOWED | Direct XTZ transfer rejected |
| CONSENSUS_ALREADY_EXECUTED | Consensus already triggered |
| *_ALREADY_VOTED | Party already voted |

## Security Invariants

1. **Funds Safety**: Transfers only in terminal states via centralized `_settle()` using `sp.balance`
2. **State Consistency**: Valid FSM transitions only
3. **Authorization**: Enforced sender checks
4. **Time Safety**: Funds recoverable at or after deadline (`now >= deadline`)
5. **No Fund-Locking**: Multiple exit paths guaranteed
