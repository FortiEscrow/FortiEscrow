# FortiEscrow

A reusable escrow smart contract framework for Tezos and Etherlink. FortiEscrow standardizes escrow semantics as a composable trust primitive for decentralized applications.

## Core Properties

- **No Super-Admin**: No privileged role can unilaterally control funds
- **Anti-Fund-Locking**: Timeout-based permissionless recovery
- **Explicit FSM**: Deterministic state transitions with validation
- **Defense in Depth**: Multiple validation layers on every entrypoint

## State Machine

```
INIT ──[fund]──> FUNDED ──[release]──> RELEASED (terminal)
                    │
                    └──[refund]──────> REFUNDED (terminal)
                    └──[force_refund]─> REFUNDED (after timeout)
```

## Quick Start

```bash
pip install smartpy
git clone https://github.com/your-org/FortiEscrow-Labs.git
cd FortiEscrow-Labs
```

```python
from contracts.core.escrow_base import SimpleEscrow
import smartpy as sp

escrow = SimpleEscrow(
    depositor=sp.address("tz1Alice..."),
    beneficiary=sp.address("tz1Bob..."),
    amount=sp.nat(5_000_000),        # 5 XTZ
    timeout_seconds=sp.nat(604800)   # 7 days
)
```

## Usage

```python
# Fund escrow (depositor only, exact amount)
escrow.fund().run(sender=depositor, amount=sp.mutez(5_000_000))

# Release to beneficiary (depositor only, before deadline)
escrow.release().run(sender=depositor)

# Refund to depositor (depositor only)
escrow.refund().run(sender=depositor)

# Force refund (anyone, after deadline)
escrow.force_refund().run(sender=anyone)
```

## Documentation

| Document | Description |
|----------|-------------|
| [docs/SEMANTICS.md](docs/SEMANTICS.md) | State machine, transitions, invariants |
| [docs/SECURITY.md](docs/SECURITY.md) | Threat model, authorization matrix |
| [docs/API.md](docs/API.md) | Entrypoints, views, error codes |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Deployment and integration guide |
| [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) | Contribution guidelines |

## Security Invariants

1. **Funds Safety**: Transfers only in terminal states
2. **State Consistency**: Valid FSM transitions only
3. **Authorization**: Enforced sender checks
4. **Time Safety**: Funds recoverable after deadline
5. **No Fund-Locking**: Multiple exit paths

## Testing

```bash
pytest tests/ -v
```

## Project Structure

```
contracts/
├── core/
│   ├── escrow_base.py      # Base contract + SimpleEscrow
│   ├── escrow_multisig.py  # Multi-signature variant
│   └── escrow_factory.py   # Factory pattern
├── interfaces/
│   ├── types.py            # Type definitions
│   └── errors.py           # Error codes
└── variants/               # Extended variants
```

## License

MIT
