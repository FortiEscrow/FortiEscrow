# Unit Tests

Test individual functions and entrypoints.

## Files

- `test_fund_escrow.py` - fund_escrow() tests
- `test_release_funds.py` - release_funds() tests
- `test_refund_escrow.py` - refund_escrow() tests
- `test_force_refund.py` - force_refund() tests
- `test_views.py` - View function tests

## Coverage

### test_fund_escrow.py
- ✅ Successful funding
- ✅ Double-funding prevention
- ✅ Amount validation (under/over)
- ✅ State transition validation

### test_release_funds.py
- ✅ Successful release
- ✅ Authorization check (depositor only)
- ✅ State validation (FUNDED only)
- ✅ Timeout check (can't release after timeout)

### test_refund_escrow.py
- ✅ Successful refund
- ✅ Authorization check (depositor only)
- ✅ State validation
- ✅ Early refund behavior

### test_force_refund.py
- ✅ Permissionless recovery
- ✅ Timeout validation
- ✅ Premature recovery prevention
- ✅ Fund return guarantee

### test_views.py
- ✅ get_status() accuracy
- ✅ can_transition() correctness
- ✅ Timeout expired flag

---

**Last Updated**: January 25, 2026
