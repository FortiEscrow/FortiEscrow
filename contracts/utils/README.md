# FortiEscrow Utilities

Helper functions and adapters.

## Files

- **`amount_validator.py`** - Amount validation
- **`timeline_manager.py`** - Timeout and timeline helpers
- **`__init__.py`** - Module exports

## Amount Validator

```python
from contracts.utils import amount_validator

# Validate positive amount
amount_validator.validate_positive_amount(sp.nat(1_000_000))

# Validate exact funding
amount_validator.validate_exact_funding(sp.amount, expected_amount)

# Validate reasonable bounds
amount_validator.validate_amount_is_reasonable(sp.nat(5_000_000))
```

**Functions**:
- `validate_positive_amount(amount)` - Check amount > 0
- `validate_exact_funding(received, expected)` - Check exact match
- `validate_amount_is_reasonable(amount)` - Check within bounds

## Timeline Manager

```python
from contracts.utils import timeline_manager

# Calculate timeout expiration
expiration = timeline_manager.calculate_timeout_expiration(
    funded_timestamp, timeout_seconds
)

# Check if expired
is_expired = timeline_manager.is_timeout_expired(
    funded_timestamp, timeout_seconds
)

# Validate timeout parameters
timeline_manager.validate_minimum_timeout(timeout_seconds)
timeline_manager.validate_reasonable_timeout(timeout_seconds)
```

**Functions**:
- `calculate_timeout_expiration(funded_timestamp, timeout_seconds)`
- `is_timeout_expired(funded_timestamp, timeout_seconds)`
- `validate_minimum_timeout(timeout_seconds)` - Check >= 1 hour
- `validate_reasonable_timeout(timeout_seconds)` - Check <= 1 year

## Usage Pattern

Use utilities to avoid code duplication across variants:

```python
from contracts.utils import amount_validator, timeline_manager

class FortiEscrowCustom(FortiEscrow):
    def custom_entrypoint(self):
        # Reuse utilities
        amount_validator.validate_positive_amount(some_amount)
        is_expired = timeline_manager.is_timeout_expired(ts, timeout)
```

---

**Last Updated**: January 25, 2026
