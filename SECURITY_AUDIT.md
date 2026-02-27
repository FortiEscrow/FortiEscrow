# FortiEscrow Security Audit Report

**Auditor:** Claude Sonnet 4.6 (AI-assisted)
**Date:** 2026-02-27
**Scope:** `contracts/core/escrow_base.py`, `contracts/core/escrow_factory.py`, `contracts/core/escrow_multisig.py`, `contracts/adapters/escrow_adapter.py`
**Framework:** Tezos/SmartPy (mock environment for testing)

---

## Executive Summary

FortiEscrow's smart contract architecture is **fundamentally sound**. The CEI (Checks–Effects–Interactions) pattern is consistently applied across all settlement paths. No fund-theft, reentrancy, or privilege-escalation vectors were found.

**Two medium-severity vulnerabilities** in `EscrowFactory` can cause accidental permanent fund loss. Three low-severity view inconsistencies exist in `EscrowBase`. One informational documentation mismatch in `EscrowMultiSig`.

All findings have been patched. Tests pass after patching.

---

## Severity Definitions

| Level    | Definition |
|----------|-----------|
| CRITICAL | Direct fund theft, unauthorized access to funds |
| HIGH     | Permanent fund lock, privilege escalation |
| MEDIUM   | Accidental fund loss (user error), logic errors with economic impact |
| LOW      | View/API misleading output, minor logic gaps |
| INFO     | Documentation inconsistency, no runtime impact |

---

## Findings

### F-01 — View `can_release` Uses Inclusive Deadline Boundary

| Field | Value |
|-------|-------|
| **File** | `contracts/core/escrow_base.py` |
| **Line** | 621 |
| **Severity** | LOW |
| **Type** | View Inconsistency |

**Description:**
`get_status()` computes `can_release` using `sp.now <= self.data.deadline` (inclusive), but `release()` enforces `sp.now < self.data.deadline` (strictly less than).

At the exact deadline moment:
- View reports `can_release = True` ← **misleading**
- `release()` call fails with `ESCROW_DEADLINE_PASSED` ← **actual behavior**

```
sp.now == deadline:
  get_status().can_release  → True  (sp.now <= deadline → True)   ← WRONG
  release()                 → FAIL  (sp.now < deadline  → False)  ← ACTUAL
```

**Patch:** Change `<=` to `<` in `get_status()` line 621.

---

### F-02 — View `can_force_refund` Uses Exclusive Deadline Boundary

| Field | Value |
|-------|-------|
| **File** | `contracts/core/escrow_base.py` |
| **Line** | 618 |
| **Severity** | LOW |
| **Type** | View Inconsistency |

**Description:**
`get_status()` computes `timeout_expired` using `sp.now > self.data.deadline` (strictly greater), but `force_refund()` enforces `sp.now >= self.data.deadline` (at or after).

At the exact deadline moment:
- View reports `can_force_refund = False` ← **misleading**
- `force_refund()` call **succeeds** ← **actual behavior**

```
sp.now == deadline:
  get_status().can_force_refund → False (sp.now > deadline  → False) ← WRONG
  force_refund()                → OK    (sp.now >= deadline → True)  ← ACTUAL
```

**Patch:** Change `sp.now > self.data.deadline` to `sp.now >= self.data.deadline` on line 618.

---

### F-03 — `EscrowFactory.create_escrow()` Missing `sp.amount == 0` Guard

| Field | Value |
|-------|-------|
| **File** | `contracts/core/escrow_factory.py` |
| **Line** | 119–183 |
| **Severity** | MEDIUM |
| **Type** | Accidental Fund Lock |

**Description:**
`EscrowFactory.create_escrow()` does not verify that no XTZ is attached to the call. If a user accidentally attaches XTZ, those funds are transferred to the factory contract and **permanently locked** — the factory has no withdrawal mechanism.

Compare with `EscrowAdapter.create_escrow()` which correctly guards:
```python
sp.verify(sp.amount == sp.tez(0), EscrowError.AMOUNT_MISMATCH)  # ← PRESENT in adapter
# ← ABSENT in factory
```

**Fund Lock Proof:**
```
User calls: factory.create_escrow({...}).with_amount(100_mutez)
  → 100 mutez sent to factory contract
  → Factory has no withdrawal entry point
  → 100 mutez permanently locked
```

**Patch:** Add `sp.verify(sp.amount == sp.tez(0), EscrowError.AMOUNT_MISMATCH)` as the first check in `create_escrow()`.

---

### F-04 — `EscrowFactory` Missing `default()` Rejection

| Field | Value |
|-------|-------|
| **File** | `contracts/core/escrow_factory.py` |
| **Line** | (absent — no `default()` entry point) |
| **Severity** | MEDIUM |
| **Type** | Accidental Fund Lock |

**Description:**
`EscrowFactory` has no `default()` entry point. In Tezos, a contract without `default()` accepts direct XTZ transfers. Any XTZ sent directly to the factory address is permanently locked.

`EscrowBase` correctly implements this protection; the factory does not.

**Fund Lock Proof:**
```
User sends: 500_000 mutez → factory_address  (direct transfer)
  → Factory accepts (no default() rejection)
  → 500_000 mutez permanently locked
```

**Patch:** Add `default()` entry point that calls `sp.failwith(EscrowError.DIRECT_TRANSFER_NOT_ALLOWED)`.

---

### F-05 — `_is_timeout_expired()` Docstring Semantically Inverted

| Field | Value |
|-------|-------|
| **File** | `contracts/core/escrow_base.py` |
| **Line** | 233 |
| **Severity** | INFO |
| **Type** | Documentation |

**Description:**
Docstring reads: *"Returns True when deadline is AT or AFTER now."*
Correct reading: *"Returns True when now is AT or AFTER deadline."*

Code `return sp.now >= self.data.deadline` is correct. Documentation-only issue.

---

### F-06 — Vote-Change Docstring Contradicts Implementation

| Field | Value |
|-------|-------|
| **File** | `contracts/core/escrow_multisig.py` |
| **Lines** | 695, 767 |
| **Severity** | LOW |
| **Type** | Documentation Inconsistency |

**Description:**
Both `vote_release()` and `vote_refund()` docstrings claim *"Vote change NOT allowed after initial vote"*, but the implementation explicitly handles vote changes with count adjustment logic.

Vote changes are safe because `_check_consensus()` fires immediately after each vote and `consensus_executed` prevents re-execution. However, the docstring is false and misleads auditors.

**Patch:** Update docstrings to reflect that vote changes are allowed.

---

## CEI Pattern Verification

### EscrowBase / SimpleEscrow

| Entry Point | Checks | Effects | Interactions | Compliant |
|------------|--------|---------|--------------|-----------|
| `fund()` | state==INIT, sender==depositor, amount exact | state=FUNDED, funded_at, deadline | _(none)_ | ✅ |
| `release()` | state==FUNDED, sender==depositor, now<deadline | state=RELEASED | `_transfer_to_beneficiary()` | ✅ |
| `refund()` | state==FUNDED, sender==depositor | state=REFUNDED | `_transfer_to_depositor()` | ✅ |
| `force_refund()` | state==FUNDED, now>=deadline | state=REFUNDED | `_settle(depositor)` | ✅ |
| `default()` | _(none)_ | _(none)_ | `sp.failwith(...)` | ✅ |

**No code executes after `sp.send()` in any entry point.**

### MultiSigEscrow

| Entry Point | Checks | Effects | Interactions | Compliant |
|------------|--------|---------|--------------|-----------|
| `vote_release()` | state==FUNDED, !consensus_executed, is_party | vote counts, voted flags | `_check_consensus()` → settle | ✅ |
| `vote_refund()` | state==FUNDED, !consensus_executed, is_party | vote counts, voted flags | `_check_consensus()` → settle | ✅ |
| `raise_dispute()` | state==FUNDED, is_party, no active dispute | dispute_state=PENDING | _(none)_ | ✅ |
| `resolve_dispute()` | is_arbiter, DISPUTE_PENDING, FUNDED, valid_outcome | dispute_state=RESOLVED | `_execute_release/refund()` | ✅ |
| `force_refund()` | state==FUNDED, now>=deadline | state=REFUNDED | `_settle(depositor)` | ✅ |

---

## Fund Lock Analysis

| Scenario | Pre-Patch | Post-Patch |
|----------|-----------|------------|
| Depositor absent, never releases | `force_refund()` by anyone after deadline | ✅ Same |
| All 3 multisig parties unresponsive | `force_refund()` after deadline | ✅ Same |
| Arbiter fails to resolve dispute in time | `force_refund()` after escrow deadline | ✅ Same |
| Factory: XTZ attached to create_escrow() | **LOCKED permanently** | ✅ Rejected (F-03) |
| Factory: direct XTZ transfer to factory | **LOCKED permanently** | ✅ Rejected (F-04) |

**After patches: no permanent fund lock is possible in any scenario.**

---

## Privilege Escalation Analysis

| Actor | Can Do | Cannot Do |
|-------|--------|-----------|
| Depositor | fund, release (before deadline), refund, vote (multisig) | Cannot steal — refund returns to depositor |
| Beneficiary | vote (multisig only) | Cannot call release/refund in SimpleEscrow |
| Arbiter | vote, resolve_dispute (when DISPUTE_PENDING) | Cannot unilaterally release; cannot resolve without open dispute |
| Anyone | force_refund (after deadline) | Cannot redirect funds — dest hardcoded to depositor at init |
| Adapter | create escrow (factory role only) | fund/release/refund are disabled with `sp.failwith` |

**No privilege escalation found.** The arbiter role is strictly bounded and auditable.

---

## Strict Deadline Comparison Summary

| Location | Operation | Comparison | Correct? |
|----------|-----------|-----------|---------|
| `escrow_base.py:425` | `release()` | `sp.now < deadline` | ✅ |
| `escrow_base.py:554` | `force_refund()` | `sp.now >= deadline` | ✅ |
| `escrow_base.py:618` | view `can_force_refund` | `sp.now > deadline` (pre-patch) → `>=` (patched) | ✅ patched |
| `escrow_base.py:621` | view `can_release` | `sp.now <= deadline` (pre-patch) → `<` (patched) | ✅ patched |
| `escrow_multisig.py:1118` | `force_refund()` | `sp.now >= deadline` | ✅ |

---

## Patch Summary

| ID | File | Line | Change | Fixes |
|----|------|------|--------|-------|
| P-01 | `escrow_base.py` | 621 | `<=` → `<` in `can_release` | F-01 (LOW) |
| P-02 | `escrow_base.py` | 618 | `>` → `>=` in `timeout_expired` | F-02 (LOW) |
| P-03 | `escrow_base.py` | 233 | Fix inverted docstring | F-05 (INFO) |
| P-04 | `escrow_factory.py` | 143 | Add `sp.amount == sp.tez(0)` guard | F-03 (MEDIUM) |
| P-05 | `escrow_factory.py` | (new) | Add `default()` entry point | F-04 (MEDIUM) |
| P-06 | `escrow_multisig.py` | 695, 767 | Fix vote-change docstrings | F-06 (LOW) |
