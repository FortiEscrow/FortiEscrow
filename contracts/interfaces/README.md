# FortiEscrow Interfaces

Shared type definitions, error codes, and events.

## Files

- **`types.py`** - Type definitions
- **`errors.py`** - Error codes
- **`events.py`** - Event definitions
- **`__init__.py`** - Module exports

## Type Definitions

```python
from contracts.interfaces import types

# State constants
types.STATE_INIT          # "INIT"
types.STATE_FUNDED        # "FUNDED"
types.STATE_RELEASED      # "RELEASED"
types.STATE_REFUNDED      # "REFUNDED"

# Records for structured data
types.PartyInfo      # depositor, beneficiary, relayer
types.EscrowParams   # escrow_amount, timeout_seconds
types.EscrowState    # state, funded_timestamp, is_locked
```

## Error Codes

```python
from contracts.interfaces.errors import FortiEscrowError

# Use in contracts
sp.verify(condition, FortiEscrowError.INVALID_STATE)
sp.verify(amount > 0, FortiEscrowError.ZERO_AMOUNT)
sp.verify(sender == depositor, FortiEscrowError.UNAUTHORIZED)
```

**Available Errors**:
- `INVALID_STATE` - Wrong state for operation
- `UNAUTHORIZED` - Caller not authorized
- `INSUFFICIENT_FUNDS` - Amount doesn't match
- `INVALID_PARAMETERS` - Invalid parameters
- `TIMEOUT_NOT_REACHED` - Timeout hasn't expired
- `TIMEOUT_EXCEEDED` - Timeout has passed
- `ZERO_AMOUNT` - Amount is zero
- `DUPLICATE_PARTY` - Same address used twice

## Events

```python
from contracts.interfaces.events import (
    FundedEvent,
    ReleasedEvent,
    RefundedEvent,
    ForcedRefundEvent
)

# Emit when state changes
sp.emit(FundedEvent())
sp.emit(ReleasedEvent())
```

## Design Principle

**Single Source of Truth**: All shared definitions in one place.

- Core contract imports from `interfaces/`
- Variants import from `interfaces/`
- Tests import from `interfaces/`
- No duplication = no inconsistencies

---

**Last Updated**: January 25, 2026
