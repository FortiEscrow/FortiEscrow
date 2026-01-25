# Integration Tests

Test complete workflows and scenarios.

## Files

- `test_happy_path.py` - Complete happy path flows
- `test_timeout_recovery.py` - Timeout-driven recovery
- `test_multi_escrow.py` - Multiple escrows

## Scenarios

### Happy Path
- Fund → Release (complete)
- Fund → Refund (early abort)

### Timeout Recovery
- Fund → Wait → Force-refund
- Recover after depositor disappears

### Multi-Escrow
- Create multiple escrows
- Independent state tracking
- Simultaneous operations

---

**Last Updated**: January 25, 2026
