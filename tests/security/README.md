# Security Tests

Security-focused tests for attack prevention.

## Files

- `test_authorization.py` - Authorization bypass attempts
- `test_fund_locking.py` - Fund-locking prevention
- `test_state_machine.py` - FSM violation attempts
- `test_amount_validation.py` - Amount edge cases

## Coverage

### Authorization Tests
- ❌ Beneficiary release attempt
- ❌ Relayer refund attempt
- ❌ Attacker access attempts

### Fund-Locking Tests
- ✅ Timeout enables recovery
- ✅ Permissionless force-refund
- ✅ Funds always returnable

### State Machine Tests
- ❌ Double-funding prevention
- ❌ Release from INIT prevention
- ❌ Invalid state transitions

### Amount Validation Tests
- ❌ Under-funding rejection
- ❌ Over-funding rejection
- ✅ Exact amount required

---

**Last Updated**: January 25, 2026
