# API Reference

For integration and development.

## Contents

### Core Contract
`core_contract.md` - Complete core contract API

### Error Codes
`error_codes.md` - All error codes and meanings

### Type Definitions
`type_definitions.md` - Type definitions and structures

## Quick Reference

```python
# Import contract
from contracts.core import forti_escrow

# Create contract
contract = forti_escrow.FortiEscrow(
    depositor=sp.address("tz1..."),
    beneficiary=sp.address("tz1..."),
    relayer=sp.address("tz1..."),
    escrow_amount=sp.nat(1_000_000),
    timeout_seconds=sp.nat(7*24*3600)
)

# Call entrypoint
contract.fund_escrow()
contract.release_funds()
contract.refund_escrow()
contract.force_refund()

# Query views
contract.get_status()
contract.can_transition("RELEASED")
```

See `core_contract.md` for complete documentation.

---

**Last Updated**: January 25, 2026
