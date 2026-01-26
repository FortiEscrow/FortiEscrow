# FortiEscrow

A reusable escrow smart contract framework for Tezos and Etherlink. FortiEscrow standardizes escrow semantics as a composable trust primitive for decentralized applications.

## Core Properties

FortiEscrow implements a deterministic finite state machine with the following guarantees:

1. **No Super-Admin**: No privileged role can unilaterally control funds
2. **Anti-Fund-Locking**: Timeout-based permissionless recovery ensures funds are never permanently locked
3. **Explicit FSM**: All state transitions are validated and deterministic
4. **Defense in Depth**: Multiple validation layers on every entrypoint

## State Machine

```
INIT ──[fund]──> FUNDED ──[release]──> RELEASED (terminal)
                    │
                    └──[refund]──────> REFUNDED (terminal)
                    └──[force_refund]─> REFUNDED (terminal, after timeout)
```

## Quick Start

```python
from contracts.core.escrow_base import SimpleEscrow
import smartpy as sp

escrow = SimpleEscrow(
    depositor=sp.address("tz1Alice..."),
    beneficiary=sp.address("tz1Bob..."),
    amount=sp.nat(5_000_000),        # 5 XTZ in mutez
    timeout_seconds=sp.nat(604800)   # 7 days
)
```

## Documentation

| Document | Description |
|----------|-------------|
| [SEMANTICS.md](SEMANTICS.md) | State machine, transitions, invariants |
| [SECURITY.md](SECURITY.md) | Threat model, authorization matrix |
| [API.md](API.md) | Entrypoints, views, error codes |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Deployment and integration guide |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guidelines |

## Contract Variants

| Variant | Location | Description |
|---------|----------|-------------|
| SimpleEscrow | `contracts/core/escrow_base.py` | Basic two-party escrow |
| MultisigEscrow | `contracts/core/escrow_multisig.py` | Multi-signature release |
| MilestoneEscrow | `contracts/variants/milestone/` | Phased release |
| TokenEscrow | `contracts/variants/token/` | FA1.2/FA2 token support |

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

tests/
├── test_fortiescrow.py     # Core test suite
├── test_invariants.py      # Invariant verification
└── test_security_fixes.py  # Security regression tests
```

## Requirements

- Python 3.8+
- SmartPy 0.17+

## License

MIT
