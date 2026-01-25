# FortiEscrow Variants

Framework extensions building on core contract.

## Available Variants

### Token Variant (`token/`)

**Purpose**: Support FA1.2/FA2 token escrow (not just XTZ)

```python
from contracts.variants.token import forti_escrow_token

contract = forti_escrow_token.FortiEscrowToken(
    depositor=sp.address("tz1..."),
    beneficiary=sp.address("tz1..."),
    relayer=sp.address("tz1..."),
    token_address=sp.address("KT1..."),  # FA1.2 token
    token_amount=sp.nat(100),
    timeout_seconds=sp.nat(7*24*3600)
)
```

**Status**: 🔄 Planned (v1.1)

### Atomic Swap Variant (`atomic_swap/`)

**Purpose**: Cross-chain escrow with HTLC (Hash Time Locked Contract)

```python
from contracts.variants.atomic_swap import forti_escrow_atomic

contract = forti_escrow_atomic.FortiEscrowAtomicSwap(
    depositor=sp.address("tz1..."),
    beneficiary=sp.address("tz1..."),
    secret_hash=bytes(...),  # SHA256(secret)
    escrow_amount=sp.nat(1_000_000),
    timeout_seconds=sp.nat(48*3600)  # 48 hours for cross-chain
)
```

**Status**: 🔄 Planned (v1.2)

### Milestone Variant (`milestone/`)

**Purpose**: Staged releases (e.g., 25% every milestone)

```python
from contracts.variants.milestone import forti_escrow_milestone

contract = forti_escrow_milestone.FortiEscrowMilestone(
    depositor=sp.address("tz1..."),
    beneficiary=sp.address("tz1..."),
    relayer=sp.address("tz1..."),
    escrow_amount=sp.nat(4_000_000),  # 4 XTZ total
    milestones=[
        {"percentage": 25, "deadline": sp.timestamp(...)},
        {"percentage": 25, "deadline": sp.timestamp(...)},
        {"percentage": 25, "deadline": sp.timestamp(...)},
        {"percentage": 25, "deadline": sp.timestamp(...)},
    ]
)
```

**Status**: 🔄 Planned (v1.3)

---

## Creating a New Variant

See `/docs/developer_guide/extending_framework.md` for complete guide.

### Template

1. **Inherit from core**: Extend FortiEscrow class
2. **Override as needed**: Add variant-specific logic
3. **Preserve invariants**: Security properties must still hold
4. **Write tests**: Add tests in `/tests/`
5. **Document**: Add README and API reference

### Example

```python
from contracts.core import forti_escrow
import smartpy as sp

class FortiEscrowCustom(forti_escrow.FortiEscrow):
    """Custom variant with additional features"""
    
    def __init__(self, ...):
        super().__init__(...)
        # Variant-specific initialization
    
    @sp.entrypoint
    def custom_action(self):
        """Variant-specific entrypoint"""
        # Your logic here
        pass
```

---

## Version Matrix

| Variant | Version | Status | Target |
|---------|---------|--------|--------|
| Core | 1.0.0 | ✅ Ready | Now |
| Token | 1.1.0 | 🔄 Planned | Q1 2026 |
| Atomic | 1.2.0 | 🔄 Planned | Q2 2026 |
| Milestone | 1.3.0 | 🔄 Planned | Q2 2026 |

---

**Last Updated**: January 25, 2026
