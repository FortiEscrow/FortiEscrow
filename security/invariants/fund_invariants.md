# Fund Invariants

## Property

**Contract balance must always equal escrow_amount in FUNDED state, and be zero in terminal states.**

## Formal Statement

For all contract states:
- INIT: balance = 0
- FUNDED: balance = escrow_amount
- RELEASED: balance = 0 (funds transferred to beneficiary)
- REFUNDED: balance = 0 (funds transferred to depositor)

No funds are lost or trapped.

## Proof

### Balance Flow Analysis

**Initial State (INIT)**
- Contract created with balance = 0
- No funds deposited yet

**After Funding (FUNDED)**
- Line 224: Exact amount validation: `sp.amount == sp.utils.nat_to_tez(escrow_amount)`
- Balance = escrow_amount (enforced by protocol)
- No other operations modify balance while FUNDED

**After Release (RELEASED)**
- Line 268: All funds transferred: `sp.send(beneficiary, funds)`
- Balance = 0 after transfer
- State = RELEASED (no further operations allowed)

**After Refund (REFUNDED)**
- Line 355 or 378: All funds transferred: `sp.send(depositor, funds)`
- Balance = 0 after transfer
- State = REFUNDED (no further operations allowed)

### Mathematical Proof

Let B(t) = contract balance at time t

**Initial**: B(0) = 0

**After fund_escrow()**:
- Amount transferred: sp.amount = escrow_amount (verified)
- B(t1) = B(0) + escrow_amount = escrow_amount ✓

**After release_funds()**:
- Amount transferred to beneficiary: escrow_amount
- B(t2) = B(t1) - escrow_amount = 0 ✓

**After refund_escrow() or force_refund()**:
- Amount transferred to depositor: escrow_amount
- B(t3) = B(t1) - escrow_amount = 0 ✓

### Atomic Transfers

SmartPy guarantees atomic execution:
- State changes and transfers are atomic
- Either both succeed or both fail
- No partial state (e.g., RELEASED but balance != 0)

## Code References

- [forti_escrow.py line 224](../contracts/core/forti_escrow.py#L224) - Amount validation
- [forti_escrow.py line 268](../contracts/core/forti_escrow.py#L268) - Release transfer
- [forti_escrow.py line 355](../contracts/core/forti_escrow.py#L355) - Refund transfer
- [forti_escrow.py line 378](../contracts/core/forti_escrow.py#L378) - Force refund transfer

## Test Coverage

- ✅ `tests/unit/test_amount_validation.py` - Amount exactness
- ✅ `tests/security/test_fund_invariants.py` - Balance consistency
- ✅ `tests/integration/test_happy_path.py` - Complete flows

---

**Status**: ✅ Proven & Verified  
**Last Updated**: January 25, 2026
