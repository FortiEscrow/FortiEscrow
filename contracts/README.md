# FortiEscrow Contracts

Core smart contract implementations for the FortiEscrow framework.

## Structure

- **`core/`** - Base escrow contract (immutable, audited)
- **`variants/`** - Framework extensions (token, atomic swap, milestone-based)
- **`interfaces/`** - Shared types, errors, events
- **`utils/`** - Utility adapters (amount validation, timeline management)

## Core Contract

The main escrow contract in `core/forti_escrow.py` implements:

- Explicit finite state machine (INIT → FUNDED → RELEASED/REFUNDED)
- No super-admin or unilateral fund control
- Anti-fund-locking via timeout recovery
- Comprehensive security checks on all entrypoints

**Status**: ✅ Audited, production-ready

## Variants

Framework extensions in `variants/`:

- **Token Variant** (`token/`) - FA1.2/FA2 token escrow
- **Atomic Swap** (`atomic_swap/`) - Cross-chain HTLC variant
- **Milestone** (`milestone/`) - Staged release mechanism

Each variant extends core logic without modifying it.

## Interfaces

Shared definitions in `interfaces/`:

- **`types.py`** - Type definitions for all contracts
- **`errors.py`** - Centralized error codes
- **`events.py`** - Event definitions

Single source of truth prevents inconsistencies.

## Utilities

Helper functions in `utils/`:

- **`amount_validator.py`** - Amount validation adapters
- **`timeline_manager.py`** - Timeout and timeline helpers

Utilities are reusable across variants.

---

## Usage

### Import Core Contract

```python
from contracts.core import forti_escrow

contract = forti_escrow.FortiEscrow(
    depositor=sp.address("tz1..."),
    beneficiary=sp.address("tz1..."),
    relayer=sp.address("tz1..."),
    escrow_amount=sp.nat(1_000_000),
    timeout_seconds=sp.nat(7*24*3600)
)
```

### Create a Variant

```python
from contracts.variants.token import forti_escrow_token

# Extends core logic with token support
contract = forti_escrow_token.FortiEscrowToken(...)
```

### Use Utilities

```python
from contracts.utils import amount_validator, timeline_manager

# Validate amounts
amount_validator.validate_positive_amount(sp.nat(1_000_000))

# Check timeouts
is_expired = timeline_manager.is_timeout_expired(
    funded_timestamp, timeout_seconds
)
```

---

## Security Considerations

- Core contract path (`core/`) = immutable after audit
- Variant paths = versioned and monitored
- All changes tracked in `CHANGELOG.md`
- See `/security/` for invariants and threat model

---

**Version**: 1.0.0  
**Last Updated**: January 25, 2026
