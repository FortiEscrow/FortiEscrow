<div align="center">
  <img src="assets/FortiEscrow_logo.png" alt="FortiEscrow Logo" width="300">
</div>

# FortiEscrow

A reusable escrow smart contract framework for Tezos and Etherlink. FortiEscrow standardizes escrow semantics as a composable trust primitive for decentralized applications.

## Core Properties

- **No Super-Admin**: No privileged role can unilaterally control funds
- **Anti-Fund-Locking**: Timeout-based permissionless recovery
- **Explicit FSM**: Deterministic state transitions with validation
- **Defense in Depth**: Multiple validation layers on every entrypoint

## Contract Variants

### SimpleEscrow

Two-party escrow where the depositor controls release and refund.

```
INIT ──[fund]──> FUNDED ──[release]──> RELEASED (terminal)
                    │
                    ├──[refund]──────> REFUNDED (terminal)
                    └──[force_refund]─> REFUNDED (after timeout)
```

### MultiSigEscrow

Three-party escrow with 2-of-3 consensus voting and arbiter dispute resolution.

```
INIT ──[fund]──> FUNDED ──[vote_release x2]──> RELEASED (terminal)
                    │
                    ├──[vote_refund x2]──────> REFUNDED (terminal)
                    └──[force_refund]─────────> REFUNDED (after timeout)
```

**Parties**: Depositor, Beneficiary, Arbiter

**Consensus**: Any 2-of-3 parties must agree to release or refund. Each party votes exactly once per escrow cycle. Timeout recovery bypasses voting.

## Quick Start

```bash
pip install smartpy
git clone https://github.com/FortiEscrow/FortiEscrow.git
cd FortiEscrow
```

```python
# SimpleEscrow
from contracts.core.escrow_base import SimpleEscrow
import smartpy as sp

escrow = SimpleEscrow(
    depositor=sp.address("tz1Alice..."),
    beneficiary=sp.address("tz1Bob..."),
    amount=sp.nat(5_000_000),        # 5 XTZ
    timeout_seconds=sp.nat(604800)   # 7 days
)

# MultiSigEscrow
from contracts.core.escrow_multisig import MultiSigEscrow

escrow = MultiSigEscrow(
    depositor=sp.address("tz1Alice..."),
    beneficiary=sp.address("tz1Bob..."),
    arbiter=sp.address("tz1Charlie..."),
    amount=sp.nat(5_000_000),
    timeout_seconds=sp.nat(604800)
)
```

## Usage

### SimpleEscrow

```python
# Fund escrow (depositor only, exact amount)
escrow.fund().run(sender=depositor, amount=sp.mutez(5_000_000))

# Release to beneficiary (depositor only, strictly before deadline)
escrow.release().run(sender=depositor)

# Refund to depositor (depositor only)
escrow.refund().run(sender=depositor)

# Force refund (anyone, at or after deadline)
escrow.force_refund().run(sender=anyone)
```

### MultiSigEscrow

```python
# Fund escrow (depositor only)
escrow.fund().run(sender=depositor, amount=sp.mutez(5_000_000))

# Vote to release (any party, one vote each)
escrow.vote_release().run(sender=depositor)
escrow.vote_release().run(sender=beneficiary)  # 2-of-3 reached: auto-release

# Vote to refund (any party, one vote each)
escrow.vote_refund().run(sender=depositor)
escrow.vote_refund().run(sender=arbiter)  # 2-of-3 reached: auto-refund

# Raise dispute (depositor or beneficiary only)
escrow.raise_dispute(reason="...").run(sender=depositor)

# Force refund (anyone, at or after deadline)
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

1. **Funds Safety**: Transfers only in terminal states via centralized `_settle()` using `sp.balance`
2. **State Consistency**: Valid FSM transitions only (no backward transitions)
3. **Authorization**: Enforced sender checks on all privileged operations
4. **Time Safety**: Funds recoverable at or after deadline (`now >= deadline`)
5. **No Fund-Locking**: Multiple exit paths (release, refund, force_refund, voting consensus)

## Testing

```bash
pytest tests/ -v
```

## Project Structure

```
contracts/
├── core/
│   ├── escrow_base.py              # Base contract + SimpleEscrow
│   ├── escrow_multisig.py          # 2-of-3 multi-signature escrow
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

tests/
├── unit/                           # Unit tests
├── adversarial/                    # Attack scenario tests
└── invariant/                      # Invariant verification tests
```

## License

MIT
