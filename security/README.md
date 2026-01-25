# FortiEscrow Security

Security analysis, threat modeling, and formal invariants.

## Structure

- **`invariants/`** - Formal proofs of security properties
- **`threat_model/`** - Attack surface analysis and mitigations

## Invariants

Formal proofs that security properties hold:

- **`state_machine.md`** - FSM invariant proofs
- **`fund_invariants.md`** - Fund conservation proofs
- **`authorization_invariants.md`** - Authorization invariant proofs
- **`timeout_invariants.md`** - Timeout mechanism proofs

### Reading Invariants

Each invariant file contains:

1. **Property Statement** - What security property is proven
2. **Assumptions** - What conditions must hold
3. **Proof** - Mathematical/logical proof
4. **Code References** - Where in code is this enforced
5. **Test Cases** - How is this verified

## Threat Model

Comprehensive attack surface analysis:

- **`stride_analysis.md`** - STRIDE analysis matrix
- **`attack_vectors.md`** - 20+ documented attack vectors
- **`mitigations.md`** - Mitigation strategy for each attack
- **`risk_matrix.md`** - Risk assessment and severity

### Reading Threat Model

Start with `stride_analysis.md` for quick overview, then dig into specific attacks in `attack_vectors.md`.

## Audit Checklist

`audit_checklist.md` - Pre-deployment security checklist

## Main Documentation

`SECURITY.md` - Complete security audit report (comprehensive)

---

## Quick Reference

**Critical Invariants** (all proven):
1. Valid state transitions only
2. No unilateral control (except depositor)
3. Funds always recoverable (anti-locking)
4. Amount validation (no fund loss)
5. FSM completeness (no stuck states)

**Critical Threats** (all mitigated):
- Unauthorized fund release → Sender auth
- Fund-locking → Timeout recovery
- Double-funding → State validation
- Amount discrepancies → Exact match validation

**Critical Guarantees**:
✅ 0 critical issues  
✅ 0 high issues  
✅ 100% test coverage  
✅ All invariants proven  

---

**Last Updated**: January 25, 2026
