# Contracts

Smart contract implementations for the FortiEscrow framework.

## Structure

```
contracts/
├── core/
│   ├── escrow_base.py          # Base contract + SimpleEscrow
│   ├── escrow_factory.py       # Factory deployment pattern
│   ├── escrow_multisig.py      # Multi-signature variant
│   └── forti_escrow.py         # Legacy (deprecated)
├── interfaces/
│   ├── types.py                # Type definitions
│   ├── errors.py               # Error codes
│   └── events.py               # Event definitions
├── utils/
│   ├── validators.py           # Input validators
│   ├── amount_validator.py     # Amount validation
│   └── timeline_manager.py     # Timeout utilities
├── adapters/
│   └── escrow_adapter.py       # Adapter base class
├── variants/
│   ├── atomic_swap/            # HTLC escrow
│   ├── milestone/              # Phased release
│   └── token/                  # FA1.2/FA2 support
├── invariants.py               # Formal invariant definitions
└── invariants_enforcement.py   # Invariant checking
```

## Core Contract

**Location**: `core/escrow_base.py`

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
                    └──[refund]──────> REFUNDED (terminal)
                    └──[force_refund]─> REFUNDED (after timeout)
```

### Entrypoints

| Entrypoint | Transition | Authorization | Condition |
|------------|------------|---------------|-----------|
| fund() | INIT → FUNDED | depositor | amount == escrow_amount |
| release() | FUNDED → RELEASED | depositor | now <= deadline |
| refund() | FUNDED → REFUNDED | depositor | - |
| force_refund() | FUNDED → REFUNDED | anyone | now > deadline |

### Views

| View | Returns |
|------|---------|
| get_status() | state, parties, amount, deadline, flags |
| get_parties() | depositor, beneficiary |
| get_timeline() | funded_at, deadline, timeout_seconds, is_expired |

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

### MultisigEscrow

```python
from contracts.core.escrow_multisig import MultisigEscrow

escrow = MultisigEscrow(
    depositor=sp.address("tz1Alice..."),
    beneficiary=sp.address("tz1Bob..."),
    arbiter=sp.address("tz1Charlie..."),
    amount=sp.nat(5_000_000),
    timeout_seconds=sp.nat(604800),
    required_signatures=sp.nat(2)
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
| ESCROW_TIMEOUT_NOT_EXPIRED | Deadline not passed |
| ESCROW_DEADLINE_PASSED | Release window closed |
| ESCROW_SAME_PARTY | depositor == beneficiary |
| ESCROW_ZERO_AMOUNT | amount == 0 |
| ESCROW_TIMEOUT_TOO_SHORT | timeout < 1 hour |
| ESCROW_TIMEOUT_TOO_LONG | timeout > 1 year |

## Security Invariants

1. **Funds Safety**: Transfers only in terminal states
2. **State Consistency**: Valid FSM transitions only
3. **Authorization**: Enforced sender checks
4. **Time Safety**: Funds recoverable after deadline
5. **No Fund-Locking**: Multiple exit paths guaranteed

## Variants

| Variant | Description |
|---------|-------------|
| atomic_swap/ | Hash time-locked contract for cross-chain swaps |
| milestone/ | Multi-phase release with intermediate checkpoints |
| token/ | FA1.2/FA2 token support instead of XTZ |

## Testing

```bash
pytest tests/ -v
```

## Deprecation Notice

`core/forti_escrow.py` is deprecated. Use `core/escrow_base.py` instead.

**Reason**: forti_escrow.py calculates deadline at deployment time. escrow_base.py calculates deadline at funding time (correct behavior).

```python
# Deprecated
from contracts.core.forti_escrow import FortiEscrow

# Recommended
from contracts.core.escrow_base import SimpleEscrow
```
