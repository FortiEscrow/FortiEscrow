# FortiEscrow Documentation

A reusable escrow smart contract framework for Tezos. FortiEscrow standardizes escrow semantics as a composable trust primitive for decentralized applications.

## Core Properties

1. **No Super-Admin**: No privileged role can unilaterally control funds
2. **Anti-Fund-Locking**: Timeout-based permissionless recovery ensures funds are never permanently locked
3. **Explicit FSM**: All state transitions are validated and deterministic
4. **Defense in Depth**: Multiple validation layers on every entrypoint

## Documents

| Document | Description |
|----------|-------------|
| [SEMANTICS.md](SEMANTICS.md) | State machine, transitions, formal invariants |
| [SECURITY.md](SECURITY.md) | Threat model, trust assumptions, authorization matrix |
| [API.md](API.md) | Entrypoints, views, error codes |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Deployment and integration guide |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guidelines |

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

## Requirements

- Python 3.8+
- SmartPy >= 0.14.0
