# FortiEscrow: Quick Reference Guide

## File Structure

```
FortiEscrow-Labs/
├── forti_escrow.py          # Main contract implementation
├── test_forti_escrow.py     # Comprehensive test suite
├── README.md                # Project overview & quick start
├── SECURITY.md              # Security audit & threat modeling
├── DEPLOYMENT.md            # Integration guide & examples
├── THREAT_MODEL.md          # Detailed attack surface analysis
└── QUICK_REFERENCE.md       # This file
```

---

## State Machine at a Glance

```
INIT ──fund──> FUNDED ──release──> RELEASED
                  │
                  └──refund────> REFUNDED
                   (or force-refund after timeout)
```

---

## Entrypoints Quick Reference

| Entrypoint | Caller | From State | To State | Precondition |
|-----------|--------|-----------|----------|-------------|
| `fund_escrow()` | Anyone | INIT | FUNDED | Amount matches |
| `release_funds()` | Depositor | FUNDED | RELEASED | Timeout not expired |
| `refund_escrow()` | Depositor | FUNDED | REFUNDED | Always allowed |
| `force_refund()` | Anyone | FUNDED | REFUNDED | Timeout expired |

---

## Common Operations

### Create Escrow
```python
from forti_escrow import FortiEscrow
import smartpy as sp

escrow = FortiEscrow(
    depositor=sp.address("tz1Alice..."),
    beneficiary=sp.address("tz1Bob..."),
    relayer=sp.address("tz1Charlie..."),
    escrow_amount=sp.nat(1_000_000),      # 1 XTZ
    timeout_seconds=sp.nat(7*24*3600)     # 7 days
)
```

### Fund Escrow
```python
escrow.fund_escrow().run(
    amount=sp.utils.nat_to_tez(1_000_000),
    sender=depositor_address
)
```

### Release to Beneficiary
```python
escrow.release_funds().run(
    sender=depositor_address
)
```

### Refund to Depositor
```python
# Before timeout
escrow.refund_escrow().run(sender=depositor_address)

# After timeout (anyone can trigger)
escrow.force_refund().run(sender=any_address)
```

### Check Status
```python
status = escrow.get_status()
print(f"State: {status.state}")
print(f"Timeout expired: {status.timeout_expired}")
```

---

## Security Guarantees

✅ **No Super-Admin**  
- Depositor controls funds unilaterally
- No admin override or backdoor
- Relayer is coordinator only

✅ **No Fund-Locking**  
- Permissionless recovery after timeout
- Minimum timeout: 1 hour
- Funds always return to depositor

✅ **Explicit State Machine**  
- Only valid transitions allowed
- Cannot release from invalid state
- Cannot double-fund

✅ **Amount Validation**  
- Exact amount required (no over/under-funding)
- Balance consistency guaranteed
- No partial releases

✅ **Authorization Checks**  
- Release: depositor only
- Refund: depositor only (or timeout recovery)
- Funding: anyone (it's their money)

---

## Threat Mitigation Matrix

| Threat | Attack | Mitigation | Status |
|--------|--------|-----------|--------|
| Unauthorized release | Non-depositor calls `release_funds()` | Sender auth check | ✅ |
| Fund-locking | Funds trapped indefinitely | Timeout recovery | ✅ |
| Double-funding | Multiple funds sent | State validation | ✅ |
| Under-funding | Less than required sent | Amount validation | ✅ |
| Over-funding | More than required sent | Amount validation | ✅ |
| Early force-refund | Recovery before timeout | Timeout check | ✅ |
| Invalid beneficiary | Wrong address set | Protocol validation | ✅ |

---

## Testing Quick Start

```bash
# Run all tests
python test_forti_escrow.py

# Test categories:
# - State transitions (valid paths)
# - Authorization (sender checks)
# - Invalid transitions (FSM validation)
# - Fund amounts (validation)
# - Timeout mechanics (recovery)
# - Input validation (parameters)
# - Fund invariants (balance)
# - View functions (queries)
# - Happy path (complete flow)
# - Anti-locking (timeout recovery)
```

---

## Deployment Checklist

Before deploying to mainnet:

```
☐ Depositor address correct (no typos)
☐ Beneficiary address correct (no typos)
☐ Amount > 0 and reasonable
☐ Timeout >= 3600 seconds (1 hour)
☐ Depositor ≠ Beneficiary
☐ Tested on Ghostnet (testnet)
☐ All state transitions verified
☐ Timeout recovery tested
☐ Security audit completed
☐ Deployment documented
```

---

## Error Codes

| Error | Meaning | Solution |
|-------|---------|----------|
| `INVALID_STATE` | Wrong state for operation | Check state with `get_status()` |
| `INSUFFICIENT_FUNDS` | Amount doesn't match | Send exact amount |
| `UNAUTHORIZED` | Caller not authorized | Use correct account |
| `INVALID_PARAMETERS` | Timeout too short | Use >= 3600 seconds |
| `TIMEOUT_NOT_REACHED` | Can't force-refund yet | Wait for timeout |
| `TIMEOUT_EXCEEDED` | Depositor lost release right | Must refund or wait for recovery |
| `ZERO_AMOUNT` | Amount is 0 | Use positive amount |
| `DUPLICATE_PARTY` | Same depositor/beneficiary | Use different addresses |

---

## Key Design Decisions

### Why No Admin?
**Answer**: Admin keys are attack vectors. Escrow should be governed by rules (state machine) not people.

### Why Immutable Parties?
**Answer**: Prevents address hijacking. To change parties, deploy new contract (explicit and auditable).

### Why Timeout Recovery?
**Answer**: Prevents indefinite fund-locking. After timeout, anyone can recover funds.

### Why Depositor Unilateral Release?
**Answer**: Depositor owns the funds. Only depositor should decide final recipient.

### Why Exact Amount?
**Answer**: Prevents fund discrepancies. No ambiguity about how much is held.

### Why Minimum 1-Hour Timeout?
**Answer**: Allows dispute resolution window. Prevents flash-loan timeouts.

---

## Integration Steps

### Step 1: Compile
```bash
cd FortiEscrow-Labs
python forti_escrow.py  # Generates compiled/forti_escrow.tz
```

### Step 2: Deploy
```bash
tezos-client originate contract FortiEscrow \
  transferring 0 from <account> \
  running ./compiled/forti_escrow.tz \
  --init '<storage>' \
  --burn-cap 1
```

### Step 3: Fund
```bash
tezos-client transfer 1 from <account> \
  to KT1<contract_address> \
  --entrypoint fund_escrow
```

### Step 4: Operate
```bash
# Release funds
tezos-client call KT1<address> release_funds --burn-cap 1

# Or refund
tezos-client call KT1<address> refund_escrow --burn-cap 1
```

---

## Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| **Gas (fund)** | ~50,000 | Simple state change + transfer |
| **Gas (release)** | ~55,000 | State change + transfer |
| **Gas (refund)** | ~55,000 | State change + transfer |
| **Storage** | ~1,500 bytes | Minimal state |
| **Cost** | ~0.1 XTZ | Typical operation |

---

## Audit References

### Documents Provided
1. **README.md** - Project overview, architecture, examples
2. **SECURITY.md** - Comprehensive threat modeling & audit
3. **THREAT_MODEL.md** - Detailed attack surface analysis
4. **DEPLOYMENT.md** - Integration guide & operational procedures
5. **forti_escrow.py** - Well-commented source code
6. **test_forti_escrow.py** - Comprehensive test suite

### Audit Status
✅ **PRODUCTION READY** (v1.0.0)

---

## Contact & Support

**Questions**: Check documentation files first  
**Security Issues**: Report privately (see SECURITY.md)  
**Contributions**: Follow guidelines in README.md  

---

## Glossary

| Term | Definition |
|------|-----------|
| **Depositor** | Account funding the escrow (owns funds initially) |
| **Beneficiary** | Account receiving funds upon release |
| **Relayer** | Coordinator (non-binding, optional) |
| **FSM** | Finite State Machine (controls valid transitions) |
| **Timeout** | Time window before force-refund enabled |
| **Invariant** | Property that must hold at all times |
| **Mutez** | Smallest unit of XTZ (1 XTZ = 1,000,000 mutez) |

---

**Quick Reference v1.0**  
**Last Updated**: January 25, 2026
