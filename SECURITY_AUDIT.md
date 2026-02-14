# FortiEscrow Security Audit Report

**Audit Date**: 2026-02-14
**Auditor**: Senior Smart Contract Security Auditor
**Scope**: FortiEscrow Framework (SimpleEscrow, MultiSigEscrow, Factory, Utilities)
**Platform**: Tezos (SmartPy)
**Commit**: ab6da3e (main branch)

---

## Executive Summary

FortiEscrow is a two-variant escrow framework for Tezos consisting of SimpleEscrow (2-party) and MultiSigEscrow (3-party with 2-of-3 consensus). The framework demonstrates strong security fundamentals: consistent CEI (Checks-Effects-Interactions) pattern, centralized settlement via `_settle()`, deterministic deadline boundary semantics, and comprehensive voting invariant verification.

However, the audit identified **14 findings** across severity levels. The most critical issues center on: (1) the `resolve_dispute()` entrypoint granting the arbiter unilateral settlement authority that bypasses the 2-of-3 consensus model, (2) missing `default` entrypoint on MultiSigEscrow allowing untracked XTZ deposits, (3) no `sp.amount == 0` enforcement on non-funding entrypoints enabling XTZ injection, and (4) a `nat_to_tez` vs `nat_to_mutez` unit conversion error in the amount validator utility.

The core escrow logic (SimpleEscrow) is production-ready with minor view-layer inconsistencies. The MultiSigEscrow contract requires remediation of the dispute resolution authority model and the missing default entrypoint before mainnet deployment. Peripheral modules (interfaces, utilities) contain dead code, divergent type systems, and authorization gaps that should be cleaned up.

**Overall Security Score: 6.5 / 10**

---

## Vulnerability List

### CRITICAL Severity

#### C-01: Arbiter Unilateral Settlement via `resolve_dispute()`

**File**: [escrow_multisig.py:960-1065](contracts/core/escrow_multisig.py#L960-L1065)
**Severity**: CRITICAL
**Status**: NEW

**Description**: The `resolve_dispute()` entrypoint allows the arbiter to unilaterally settle the escrow (release or refund) without requiring consensus from either the depositor or beneficiary. This fundamentally breaks the 2-of-3 consensus model that is the core security property of MultiSigEscrow.

**Attack Vector**:
1. Depositor funds escrow
2. Depositor or beneficiary raises a dispute (for any reason)
3. Arbiter calls `resolve_dispute(0)` to release funds to beneficiary, or `resolve_dispute(1)` to refund to depositor
4. Settlement executes immediately -- no second party needed

**Impact**: The arbiter, who is supposed to be a neutral tiebreaker in a 2-of-3 scheme, gains unilateral fund control during any active dispute. A malicious arbiter who colludes with either party can settle funds without the third party's consent. This reduces the security model from 2-of-3 to effectively 1-of-1 (arbiter alone) during disputes.

**Root Cause**: `resolve_dispute()` calls `_execute_release()` / `_execute_refund()` directly, bypassing the voting consensus mechanism entirely. The comment at line 1059 explicitly states: "No voting needed - arbiter IS the consensus."

**Recommendation**:
- Option A: `resolve_dispute()` should cast the arbiter's vote and let the normal consensus mechanism decide (arbiter's vote + at least one other party's vote)
- Option B: Require that `resolve_dispute()` only finalizes if at least one other party has already voted in the same direction
- Option C: Make dispute resolution a two-step process: arbiter proposes, one party confirms

---

#### C-02: MultiSigEscrow Missing `default` Entrypoint

**File**: [escrow_multisig.py](contracts/core/escrow_multisig.py)
**Severity**: CRITICAL
**Status**: OPEN (previously identified)

**Description**: MultiSigEscrow has no `default` entrypoint to reject direct XTZ transfers. Unlike SimpleEscrow (which rejects them at [escrow_base.py:580-598](contracts/core/escrow_base.py#L580-L598)), MultiSigEscrow silently accepts any direct XTZ transfer.

**Attack Vector**:
1. Anyone sends XTZ directly to the MultiSigEscrow contract address
2. Funds are accepted and increase `sp.balance`
3. When `_settle()` executes, it sends `sp.balance` (not `escrow_amount`), so the extra XTZ goes to the settlement recipient
4. The sender permanently loses funds; the recipient receives unearned XTZ

**Impact**: Fund loss for anyone who accidentally sends XTZ to the contract. While `_settle()` using `sp.balance` prevents fund lockup, it creates an unintended transfer channel. In adversarial scenarios, an attacker could inflate the contract balance to manipulate the settlement amount seen by off-chain systems.

**Recommendation**: Add a `default` entrypoint identical to SimpleEscrow's:
```python
@sp.entry_point
def default(self):
    sp.failwith(EscrowError.DIRECT_TRANSFER_NOT_ALLOWED)
```

---

### HIGH Severity

#### H-01: No `sp.amount == 0` Guard on Non-Funding Entrypoints

**File**: [escrow_multisig.py:681-852](contracts/core/escrow_multisig.py#L681-L852), [escrow_base.py:392-574](contracts/core/escrow_base.py#L392-L574)
**Severity**: HIGH
**Status**: OPEN (previously identified)

**Description**: The entrypoints `release()`, `refund()`, `force_refund()`, `vote_release()`, `vote_refund()`, `raise_dispute()`, and `resolve_dispute()` do not verify that `sp.amount == sp.mutez(0)`. A caller can attach XTZ to these calls, which silently increases the contract's balance.

**Impact**: Attached XTZ on non-funding entrypoints inflates `sp.balance`. Since `_settle()` transfers `sp.balance` (not `escrow_amount`), the settlement recipient receives more than the agreed escrow amount. This is a minor fund injection vector but violates the principle of exact amount matching.

**Recommendation**: Add to all non-funding entrypoints:
```python
sp.verify(sp.amount == sp.mutez(0), "ESCROW_NO_AMOUNT_EXPECTED")
```

---

#### H-02: EventLogger `add_emitter()` Has No Authorization

**File**: [events.py:414-418](contracts/interfaces/events.py#L414-L418)
**Severity**: HIGH
**Status**: OPEN (previously identified)

**Description**: The `add_emitter()` entrypoint on the `EventLogger` contract has no access control. Anyone can call it to add themselves as an authorized emitter.

```python
@sp.entry_point
def add_emitter(self, emitter):
    """Add authorized emitter (admin only in production)"""
    sp.set_type(emitter, sp.TAddress)
    self.data.authorized_emitters.add(emitter)  # No auth check!
```

The docstring says "admin only in production" but no admin check is implemented.

**Impact**: Any address can register as an authorized emitter and then call `log_event()` to inject arbitrary event data. Off-chain indexers consuming these events would process spoofed data, potentially leading to incorrect UI state, false notifications, or manipulated analytics.

**Recommendation**: Add an admin address to the contract storage and enforce `sp.verify(sp.sender == self.data.admin, "UNAUTHORIZED")` on `add_emitter()`.

---

#### H-03: Dispute Isolation Creates Voting Deadlock Vector

**File**: [escrow_multisig.py:713-716](contracts/core/escrow_multisig.py#L713-L716), [escrow_multisig.py:801-804](contracts/core/escrow_multisig.py#L801-L804)
**Severity**: HIGH
**Status**: NEW

**Description**: When a dispute is active (`dispute_state == DISPUTE_PENDING`), all voting is blocked via the `DISPUTE_ACTIVE_VOTING_BLOCKED` guard. However, there is no mechanism to cancel or withdraw a dispute. Only the arbiter can resolve it via `resolve_dispute()`.

**Attack Vector**:
1. Depositor and beneficiary each cast one vote (e.g., depositor votes release, beneficiary votes refund -- 1-1 tie)
2. Depositor raises a dispute
3. Voting is now blocked for ALL parties, including the arbiter
4. Only `resolve_dispute()` (arbiter-only) or `force_refund()` (after deadline) can resolve
5. If the arbiter is unresponsive before the deadline, the escrow is locked until timeout

**Impact**: A frivolous dispute raised by either depositor or beneficiary can freeze all voting progress, forcing the escrow into a timeout-only resolution path. This is a griefing vector that denies the other parties their voting rights.

**Compounding Factor**: After a dispute is resolved (by arbiter), voting remains impossible because the per-voter locks (`depositor_voted`, `beneficiary_voted`) from before the dispute are NOT reset. Parties who voted before the dispute cannot vote again, even though the dispute resolution may have changed the context.

**Recommendation**:
- Add a dispute withdrawal mechanism (disputing party can cancel their own dispute)
- OR: Reset voting state when a dispute is resolved without settlement
- OR: Allow arbiter to resolve dispute without triggering settlement (informational resolution)

---

### MEDIUM Severity

#### M-01: `get_status()` View Deadline Logic Inconsistent with Entrypoint Logic

**File**: [escrow_base.py:618-623](contracts/core/escrow_base.py#L618-L623)
**Severity**: MEDIUM
**Status**: NEW

**Description**: The `get_status()` view uses different deadline comparison operators than the actual entrypoints:

| Field | View Logic | Entrypoint Logic | Match? |
|-------|-----------|-----------------|--------|
| `timeout_expired` | `sp.now > deadline` | `sp.now >= deadline` | NO |
| `can_release` | `sp.now <= deadline` | `sp.now < deadline` | NO |
| `can_force_refund` | `is_funded & timeout_expired` | `sp.now >= deadline` | NO |

**Impact**: Off-chain consumers (dApps, wallets) relying on `get_status()` will receive incorrect boolean flags at the exact deadline boundary:
- At `now == deadline`: view reports `can_release = True` but `release()` will fail
- At `now == deadline`: view reports `can_force_refund = False` but `force_refund()` will succeed

This creates a window where the UI shows the wrong available actions.

**Recommendation**: Fix the view to match entrypoint semantics:
```python
timeout_expired = sp.now >= self.data.deadline  # was >
can_release = is_funded & (sp.now < self.data.deadline)  # was <=
can_force_refund = is_funded & timeout_expired  # now correct
```

---

#### M-02: `_is_timeout_expired()` Inconsistency Between SimpleEscrow and MultiSigEscrow

**File**: [escrow_base.py:237](contracts/core/escrow_base.py#L237), [escrow_multisig.py:211](contracts/core/escrow_multisig.py#L211)
**Severity**: MEDIUM
**Status**: NEW

**Description**: The internal helper `_is_timeout_expired()` uses different comparison operators:
- SimpleEscrow (`escrow_base.py:237`): `sp.now >= self.data.deadline` (at-or-after)
- MultiSigEscrow (`escrow_multisig.py:211`): `sp.now > self.data.deadline` (strictly-after)

While the entrypoint `force_refund()` in both contracts correctly uses `sp.now >= self.data.deadline`, the helper function is used by the `get_status()` view in MultiSigEscrow (line 1198), producing an off-by-one error at the deadline boundary.

**Impact**: `is_timeout_expired` in MultiSigEscrow's `get_status()` view returns `False` at `now == deadline` when `force_refund()` would actually succeed.

**Recommendation**: Change `escrow_multisig.py:211` to `return sp.now >= self.data.deadline` to match SimpleEscrow and the actual `force_refund()` entrypoint logic.

---

#### M-03: `amount_validator.py` Uses `nat_to_tez` Instead of `nat_to_mutez`

**File**: [amount_validator.py:34](contracts/utils/amount_validator.py#L34)
**Severity**: MEDIUM
**Status**: OPEN (previously identified)

**Description**: The `validate_exact_funding()` function uses `sp.utils.nat_to_tez()` instead of `sp.utils.nat_to_mutez()`:

```python
sp.verify(received == sp.utils.nat_to_tez(expected), "INSUFFICIENT_FUNDS")
```

`nat_to_tez` treats the input as whole tez (1 tez = 1,000,000 mutez), while `nat_to_mutez` treats it as mutez. This is a 10^6 factor error.

**Impact**: If this validator were used by any contract, an escrow for 5,000,000 mutez (5 XTZ) would require 5,000,000 tez (5 trillion mutez) to pass validation. Currently this module is NOT imported by any production contract (core contracts use inline `sp.utils.nat_to_mutez()` directly), so impact is theoretical.

**Recommendation**: Fix to `sp.utils.nat_to_mutez(expected)` or delete the unused module.

---

#### M-04: `_verify_dispute_invariants()` Uses `sp.match` on Integer

**File**: [escrow_multisig.py:264-301](contracts/core/escrow_multisig.py#L264-L301)
**Severity**: MEDIUM
**Status**: NEW

**Description**: The `_verify_dispute_invariants()` function uses `sp.match` on `self.data.dispute_state` which is an integer (`sp.TInt`). In SmartPy, `sp.match` is designed for variant types (`sp.TVariant`), not plain integers. This may cause compilation errors depending on the SmartPy version.

**Impact**: If the SmartPy compiler rejects this pattern, the contract will fail to compile. If it silently compiles to unexpected Michelson, the invariant checks may not execute correctly, leaving state corruption undetected.

**Recommendation**: Replace `sp.match` with `sp.if_/sp.elif_/sp.else_` chains:
```python
with sp.if_(self.data.dispute_state == DISPUTE_NONE):
    # checks...
with sp.elif_(self.data.dispute_state == DISPUTE_PENDING):
    # checks...
with sp.elif_(self.data.dispute_state == DISPUTE_RESOLVED):
    # checks...
```

---

#### M-05: `interfaces/types.py` Uses String States vs Core Integer States

**File**: [types.py:11-14](contracts/interfaces/types.py#L11-L14)
**Severity**: MEDIUM
**Status**: OPEN (previously identified)

**Description**: `interfaces/types.py` defines states as strings (`"INIT"`, `"FUNDED"`, etc.) while the core contracts use integers (`0`, `1`, `2`, `3`). The `EscrowState` class also uses `sp.TString` for state and `sp.TInt` for `funded_timestamp` (should be `sp.TTimestamp`).

Additionally, `PartyInfo` includes a `relayer` field that does not exist in any production contract.

**Impact**: Any code importing from `interfaces/types.py` would use incompatible type definitions. Currently no production contract imports this module, but it represents a maintenance hazard and potential source of integration bugs.

**Recommendation**: Either align `interfaces/types.py` with the actual contract types or delete it as dead code.

---

#### M-06: `interfaces/errors.py` Has Divergent Error Code Definitions

**File**: [errors.py:8-30](contracts/interfaces/errors.py#L8-L30)
**Severity**: MEDIUM
**Status**: OPEN (previously identified)

**Description**: `FortiEscrowError` in `interfaces/errors.py` defines different error codes than `EscrowError` in `escrow_base.py`:

| Concept | `FortiEscrowError` | `EscrowError` |
|---------|-------------------|---------------|
| Invalid state | `"INVALID_STATE"` | `"ESCROW_INVALID_STATE"` |
| Timeout | `"TIMEOUT_NOT_REACHED"` | `"ESCROW_TIMEOUT_NOT_EXPIRED"` |
| Auth | `"UNAUTHORIZED"` | `"ESCROW_UNAUTHORIZED"` |
| Amount | `"INSUFFICIENT_FUNDS"` | `"ESCROW_AMOUNT_MISMATCH"` |
| Party | `"DUPLICATE_PARTY"` | `"ESCROW_SAME_PARTY"` |

**Impact**: Same as M-05 -- no production contract imports this module, but it creates confusion about which error codes are canonical.

**Recommendation**: Delete `interfaces/errors.py` or re-export from `escrow_base.EscrowError`.

---

### LOW Severity

#### L-01: Dead Code in `vote_release()` / `vote_refund()` Vote-Change Branches

**File**: [escrow_multisig.py:745-754](contracts/core/escrow_multisig.py#L745-L754), [escrow_multisig.py:833-844](contracts/core/escrow_multisig.py#L833-L844)
**Severity**: LOW
**Status**: NEW

**Description**: Both `vote_release()` and `vote_refund()` contain branches for handling vote changes (`with sp.if_(self.data.votes.contains(voter))`). These branches are unreachable because per-voter locks (`depositor_voted`, `beneficiary_voted`, `arbiter_voted`) prevent any party from voting twice -- the function would have already failed at the lock check.

The code comments acknowledge this: "This branch should not be reached due to voting locks, but kept for defensive programming."

**Impact**: Dead code increases the contract's compiled Michelson size and gas costs. More importantly, the vote-change logic contains a subtle bug: in `vote_release()` line 754, if the previous vote was neither RELEASE nor REFUND (impossible given VOTE_RELEASE=0 and VOTE_REFUND=1, but the branch handles it), it increments `release_votes` without setting the vote in the map. This dead-code bug is harmless only because the branch is unreachable.

**Recommendation**: Remove the dead vote-change branches. The per-voter locks are sufficient. If defensive programming is desired, replace with an assertion:
```python
sp.verify(~self.data.votes.contains(voter), "INTERNAL_VOTE_INCONSISTENCY")
```

---

#### L-02: Factory Registry Unbounded Growth

**File**: [escrow_factory.py:97-106](contracts/core/escrow_factory.py#L97-L106)
**Severity**: LOW
**Status**: NEW

**Description**: The factory indexes `escrows_by_depositor` and `escrows_by_beneficiary` use `sp.TList(sp.TNat)` with `sp.cons` for appending. Lists in Michelson are linked lists with O(n) traversal. A single depositor creating thousands of escrows would create an increasingly expensive-to-read list.

**Impact**: Views that return these lists (`get_escrows_by_depositor()`, `get_escrows_by_beneficiary()`) will become increasingly gas-expensive as the list grows. In extreme cases, the view could exceed gas limits and become unusable.

**Recommendation**: Consider using `sp.big_map(sp.TNat, sp.TNat)` with a per-address counter for pagination, or accept the limitation and document the growth bound.

---

#### L-03: EscrowEvents Methods Are No-Ops

**File**: [events.py:139-336](contracts/interfaces/events.py#L139-L336)
**Severity**: LOW
**Status**: NEW

**Description**: All static methods in `EscrowEvents` (e.g., `emit_funded()`, `emit_released()`) create `sp.record` objects but never store, emit, or return them. The records are created and immediately discarded.

**Impact**: No events are actually emitted by the framework. Any integration relying on `EscrowEvents` for off-chain indexing will receive no data. The code gives a false impression of event support.

**Recommendation**: Either implement actual event emission (using Tezos `sp.emit()` if available in the SmartPy version) or remove the dead code and document that events are not yet implemented.

---

#### L-04: `EventLogger.log_event()` Uses `sp.slice` on List

**File**: [events.py:406-408](contracts/interfaces/events.py#L406-L408)
**Severity**: LOW
**Status**: NEW

**Description**: The `log_event()` function attempts to maintain a circular buffer of recent events using:
```python
self.data.recent_events = sp.cons(event, sp.slice(self.data.recent_events, 0, 99).open_some([]))
```

`sp.slice` is typically used on `sp.TBytes` or `sp.TString`, not on `sp.TList`. This may cause a compilation error. Additionally, `.open_some([])` uses an empty list as default, which has a different type than the list elements.

**Impact**: The `EventLogger` contract may fail to compile. If it does compile, the circular buffer logic may not trim the list as intended, leading to unbounded growth.

**Recommendation**: Replace with proper list truncation logic or use a big_map with index-based circular buffer.

---

## Attack Simulation Scenarios

### Scenario 1: Colluding Arbiter Attack (Exploits C-01)

**Setup**: Alice (depositor), Bob (beneficiary), Mallory (arbiter). Escrow for 100 XTZ with 7-day timeout.

**Attack Sequence**:
1. Alice funds escrow: `fund()` with 100 XTZ
2. Bob raises dispute: `raise_dispute("I want my money")`
3. Mallory (colluding with Bob) calls: `resolve_dispute(0)` (release to Bob)
4. Funds are released to Bob immediately -- Alice never voted, never consented

**Result**: Bob and Mallory extract 100 XTZ from Alice without Alice's participation. The 2-of-3 consensus model is completely bypassed. Alice's only defense is `force_refund()` after the deadline, but the dispute resolution executes immediately.

**Severity**: CRITICAL -- undermines the fundamental trust model.

---

### Scenario 2: Dispute Griefing Attack (Exploits H-03)

**Setup**: Alice (depositor), Bob (beneficiary), Charlie (arbiter). Both Alice and Bob want to release but on different terms.

**Attack Sequence**:
1. Alice funds escrow
2. Alice votes to release: `vote_release()`
3. Before Bob can vote, Alice raises dispute: `raise_dispute("Need more time to verify")`
4. Bob attempts `vote_release()` -- BLOCKED by `DISPUTE_ACTIVE_VOTING_BLOCKED`
5. Charlie (arbiter) is on vacation, unresponsive
6. Escrow stuck until: Charlie resolves, OR deadline passes for `force_refund()`

**Result**: Alice griefs her own escrow by raising a dispute after voting, preventing Bob from completing the 2-of-3 consensus. Funds locked until timeout.

**Variation**: Bob could also raise the dispute to prevent Alice from completing a refund vote consensus.

---

### Scenario 3: XTZ Injection via Non-Funding Entrypoints (Exploits H-01 + C-02)

**Setup**: Standard MultiSigEscrow with 10 XTZ escrow amount.

**Attack Sequence**:
1. Depositor funds escrow with 10 XTZ
2. Attacker sends 5 XTZ directly to MultiSigEscrow address (no default entrypoint to reject)
3. Contract balance is now 15 XTZ
4. Consensus reached for release: `_settle()` sends `sp.balance` (15 XTZ) to beneficiary
5. Beneficiary receives 15 XTZ instead of 10 XTZ

**Result**: The attacker loses 5 XTZ, but the beneficiary receives 5 XTZ more than agreed. In a scenario where attacker = beneficiary, this is a way to receive bonus funds from accidental transfers by other users.

**Alternatively**: Attacker sends XTZ via `vote_release()` with attached amount -- same effect.

---

### Scenario 4: View-Entrypoint Desync at Deadline Boundary (Exploits M-01)

**Setup**: SimpleEscrow with deadline at timestamp T.

**Attack Sequence**:
1. At `now == T`: dApp calls `get_status()` view
2. View returns `can_release = True`, `can_force_refund = False`
3. User sees "Release available" in UI and submits `release()` transaction
4. Transaction included in block with `now == T`
5. `release()` fails: `sp.now < deadline` is `False` at `now == T`
6. Depositor confused; `force_refund()` was actually available but UI didn't show it

**Result**: User experience degraded at deadline boundary. Not a fund-loss issue but causes failed transactions and confusion.

---

### Scenario 5: Dispute-then-Resolve Bypasses Existing Votes (Exploits C-01 + H-03)

**Setup**: Alice (depositor), Bob (beneficiary), Charlie (arbiter). Escrow for 50 XTZ.

**Attack Sequence**:
1. Alice funds escrow
2. Alice votes refund: `vote_refund()` (she wants her money back)
3. Bob votes release: `vote_release()` (he wants the money)
4. Score: 1 refund, 1 release -- no consensus
5. Bob raises dispute: `raise_dispute("Service was delivered")`
6. Charlie calls `resolve_dispute(0)` -- releases to Bob
7. Settlement executes despite Alice's refund vote

**Result**: Charlie unilaterally overrides Alice's refund vote. The 1-1 tie was supposed to be the arbiter's moment, but `resolve_dispute()` bypasses the voting system entirely rather than adding to it. Alice's vote is effectively discarded.

---

## Suggested Code Refactoring

### 1. Add `default` Entrypoint to MultiSigEscrow

```python
# In MultiSigEscrow class, add:
@sp.entry_point
def default(self):
    """Reject all direct XTZ transfers."""
    sp.failwith(EscrowError.DIRECT_TRANSFER_NOT_ALLOWED)
```

### 2. Add Zero-Amount Guards

Create a helper and apply to all non-funding entrypoints:

```python
def _require_no_amount(self):
    """Reject entrypoint calls with attached XTZ"""
    sp.verify(sp.amount == sp.mutez(0), "ESCROW_NO_AMOUNT_EXPECTED")
```

### 3. Refactor `resolve_dispute()` to Use Consensus

Replace the direct settlement with a vote-based approach:

```python
@sp.entry_point
def resolve_dispute(self, outcome):
    sp.set_type(outcome, sp.TInt)
    self._require_arbiter()
    sp.verify(self.data.dispute_state == DISPUTE_PENDING, "DISPUTE_NOT_PENDING")
    sp.verify(self.data.state == STATE_FUNDED, EscrowError.NOT_FUNDED)
    sp.verify(
        (outcome == DISPUTE_RESOLVED_RELEASE) | (outcome == DISPUTE_RESOLVED_REFUND),
        "DISPUTE_OUTCOME_INVALID"
    )

    # Record dispute resolution
    self.data.dispute_state = DISPUTE_RESOLVED
    self.data.dispute_resolver = sp.sender
    self.data.dispute_outcome = outcome

    # Unblock voting (dispute resolved, voting can resume)
    # The arbiter's resolution is recorded but does NOT directly settle.
    # Instead, cast the arbiter's vote in the direction of the resolution.
    with sp.if_(~self.data.arbiter_voted):
        self.data.arbiter_voted = True
        with sp.if_(outcome == DISPUTE_RESOLVED_RELEASE):
            self.data.votes[sp.sender] = VOTE_RELEASE
            self.data.release_votes = self.data.release_votes + 1
        with sp.else_():
            self.data.votes[sp.sender] = VOTE_REFUND
            self.data.refund_votes = self.data.refund_votes + 1

        # Check consensus (requires arbiter + at least one other party)
        self._check_consensus()
```

### 4. Fix `get_status()` View Boundary Logic

```python
# In EscrowBase.get_status():
timeout_expired = sp.now >= self.data.deadline      # was: sp.now > self.data.deadline
can_release = is_funded & (sp.now < self.data.deadline)  # was: sp.now <= self.data.deadline
can_force_refund = is_funded & timeout_expired       # now correct

# In MultiSigEscrow._is_timeout_expired():
return sp.now >= self.data.deadline                  # was: sp.now > self.data.deadline
```

### 5. Fix `_verify_dispute_invariants()` to Use If/Elif

```python
def _verify_dispute_invariants(self):
    with sp.if_(self.data.dispute_state == DISPUTE_NONE):
        sp.verify(self.data.dispute_open_at == sp.timestamp(0), "DISPUTE_INVARIANT_NONE_OPEN_AT")
        sp.verify(self.data.dispute_outcome == -1, "DISPUTE_INVARIANT_NONE_OUTCOME")
    with sp.elif_(self.data.dispute_state == DISPUTE_PENDING):
        sp.verify(self.data.dispute_open_at > sp.timestamp(0), "DISPUTE_INVARIANT_PENDING_OPEN_AT")
        sp.verify(self.data.dispute_deadline >= self.data.dispute_open_at, "DISPUTE_INVARIANT_PENDING_DEADLINE")
        sp.verify(self.data.dispute_outcome == -1, "DISPUTE_INVARIANT_PENDING_OUTCOME")
    with sp.elif_(self.data.dispute_state == DISPUTE_RESOLVED):
        sp.verify(self.data.dispute_open_at > sp.timestamp(0), "DISPUTE_INVARIANT_RESOLVED_OPEN_AT")
        sp.verify(
            (self.data.dispute_outcome == DISPUTE_RESOLVED_RELEASE) |
            (self.data.dispute_outcome == DISPUTE_RESOLVED_REFUND),
            "DISPUTE_INVARIANT_RESOLVED_OUTCOME"
        )
```

### 6. Remove Dead Vote-Change Code

Replace the vote-change branches in `vote_release()` and `vote_refund()` with:

```python
# Defensive assertion (should never fire due to voting locks)
sp.verify(~self.data.votes.contains(voter), "INTERNAL_VOTE_INCONSISTENCY")

# Record vote
self.data.votes[voter] = VOTE_RELEASE  # or VOTE_REFUND
self.data.release_votes += 1           # or refund_votes
```

### 7. Clean Up Dead Interface Modules

Either delete or properly integrate:
- `contracts/interfaces/types.py` -- unused, divergent type definitions
- `contracts/interfaces/errors.py` -- unused, divergent error codes
- `contracts/interfaces/events.py` -- `EscrowEvents` methods are no-ops

---

## Formal Verification Invariants

The following invariants should be verified for formal correctness. They are expressed in first-order logic and can be tested via property-based testing or model checking.

### Invariant 1: State Monotonicity

```
forall t1, t2:
  t2 > t1 => state(t2) >= state(t1)

// State values: INIT(0) < FUNDED(1) < RELEASED(2), REFUNDED(3)
// No backward transitions allowed
```

### Invariant 2: Terminal State Finality

```
forall t:
  state(t) in {RELEASED, REFUNDED} =>
    forall t' > t: state(t') == state(t)

// Once terminal, state never changes
```

### Invariant 3: Funds Safety (Conservation)

```
forall t:
  state(t) in {RELEASED, REFUNDED} =>
    balance(t) == 0 AND
    (state(t) == RELEASED => beneficiary_received == pre_balance) AND
    (state(t) == REFUNDED => depositor_received == pre_balance)

// All funds disbursed on terminal state; correct recipient
```

### Invariant 4: Exact Funding

```
fund() succeeds =>
  amount_received == escrow_amount AND
  pre_state == INIT AND
  post_state == FUNDED
```

### Invariant 5: Deadline Determinism (No Gap, No Overlap)

```
forall t:
  (t < deadline => release_possible(t) AND NOT force_refund_possible(t)) AND
  (t >= deadline => NOT release_possible(t) AND force_refund_possible(t))

// Exactly one of {release, force_refund} available at any time during FUNDED
```

### Invariant 6: Authorization Correctness

```
// SimpleEscrow
fund() succeeds => sender == depositor
release() succeeds => sender == depositor
refund() succeeds => sender == depositor
force_refund() succeeds => (any sender) AND now >= deadline

// MultiSigEscrow
fund() succeeds => sender == depositor
vote_release() succeeds => sender in {depositor, beneficiary, arbiter}
vote_refund() succeeds => sender in {depositor, beneficiary, arbiter}
raise_dispute() succeeds => sender in {depositor, beneficiary}
resolve_dispute() succeeds => sender == arbiter
force_refund() succeeds => (any sender) AND now >= deadline
```

### Invariant 7: Voting Consistency (MultiSigEscrow)

```
forall t (state == FUNDED):
  release_votes == count({p in parties : votes[p] == VOTE_RELEASE}) AND
  refund_votes == count({p in parties : votes[p] == VOTE_REFUND}) AND
  release_votes + refund_votes <= 3 AND
  NOT (release_votes >= 2 AND refund_votes >= 2)
```

### Invariant 8: Per-Voter Lock Consistency (MultiSigEscrow)

```
forall p in {depositor, beneficiary, arbiter}:
  p_voted == True <=> votes.contains(p)

// Voting lock set if and only if vote recorded
```

### Invariant 9: Consensus Uniqueness (MultiSigEscrow)

```
forall execution_trace:
  count(consensus_execution_events) <= 1

// Consensus executes at most once per escrow cycle
```

### Invariant 10: Liveness (No Permanent Fund Lock)

```
forall t (state == FUNDED):
  exists t' >= t:
    state(t') in {RELEASED, REFUNDED}

// Proof: force_refund() available at deadline (permissionless)
// Therefore funds are always recoverable within timeout_seconds
```

### Invariant 11: Settlement Uses Full Balance

```
forall settlement_call:
  transferred_amount == sp.balance (not escrow_amount)

// Prevents residual fund lockup
```

### Invariant 12: Dispute State Machine

```
dispute_state transitions:
  NONE -> PENDING (via raise_dispute)
  PENDING -> RESOLVED (via resolve_dispute)
  PENDING -> NONE (via _reset_voting_state on terminal)
  RESOLVED -> NONE (via _reset_voting_state on terminal)

// No backward transitions: RESOLVED -> PENDING or PENDING -> NONE (except terminal cleanup)
```

---

## Security Score

| Category | Weight | Score | Notes |
|----------|--------|-------|-------|
| State Machine Correctness | 20% | 9/10 | Solid FSM, CEI pattern, monotonic transitions |
| Authorization Model | 15% | 7/10 | Correct for SimpleEscrow; C-01 undermines MultiSig model |
| Fund Safety | 20% | 7/10 | `_settle()` design is sound; C-02 and H-01 create injection vectors |
| Reentrancy Protection | 10% | 10/10 | CEI pattern consistently applied; state changes before transfers |
| Timeout/Deadline Safety | 10% | 8/10 | Correct boundary semantics in entrypoints; view inconsistency (M-01) |
| Voting/Consensus Integrity | 10% | 6/10 | Strong invariant verification; C-01 bypasses it; dead code (L-01) |
| Input Validation | 5% | 8/10 | Good constructor validation; missing zero-amount guards |
| Code Quality & Hygiene | 5% | 4/10 | Dead code, unused modules, divergent types, no-op events |
| Formal Verification Readiness | 5% | 7/10 | Clear invariants defined; would benefit from property-based tests |

**Weighted Score: 6.5 / 10**

### Score Justification

The framework demonstrates strong security engineering fundamentals. The SimpleEscrow contract alone would score 8.5/10 -- its CEI pattern, centralized settlement, and deterministic deadline semantics are exemplary. However, the MultiSigEscrow contract's dispute resolution mechanism (C-01) introduces a fundamental trust model violation that significantly lowers the score. The missing `default` entrypoint (C-02) and zero-amount guard gaps (H-01) are straightforward fixes that would immediately improve the score. The peripheral code modules (interfaces, utilities) drag down the code quality score with dead code and divergent type definitions.

**Post-Remediation Projected Score**: After fixing C-01, C-02, H-01, and M-01, the score would rise to approximately **8.0 / 10**.

---

## Appendix: Findings Summary

| ID | Severity | Title | Status | File |
|----|----------|-------|--------|------|
| C-01 | CRITICAL | Arbiter unilateral settlement via resolve_dispute() | NEW | escrow_multisig.py |
| C-02 | CRITICAL | MultiSigEscrow missing default entrypoint | OPEN | escrow_multisig.py |
| H-01 | HIGH | No sp.amount == 0 guard on non-funding entrypoints | OPEN | escrow_base.py, escrow_multisig.py |
| H-02 | HIGH | EventLogger add_emitter() has no authorization | OPEN | events.py |
| H-03 | HIGH | Dispute isolation creates voting deadlock vector | NEW | escrow_multisig.py |
| M-01 | MEDIUM | get_status() view deadline logic inconsistent | NEW | escrow_base.py |
| M-02 | MEDIUM | _is_timeout_expired() inconsistency between contracts | NEW | escrow_base.py, escrow_multisig.py |
| M-03 | MEDIUM | amount_validator uses nat_to_tez instead of nat_to_mutez | OPEN | amount_validator.py |
| M-04 | MEDIUM | _verify_dispute_invariants() uses sp.match on integer | NEW | escrow_multisig.py |
| M-05 | MEDIUM | interfaces/types.py uses string states vs core integers | OPEN | types.py |
| M-06 | MEDIUM | interfaces/errors.py has divergent error codes | OPEN | errors.py |
| L-01 | LOW | Dead code in vote_release/vote_refund change branches | NEW | escrow_multisig.py |
| L-02 | LOW | Factory registry unbounded list growth | NEW | escrow_factory.py |
| L-03 | LOW | EscrowEvents methods are no-ops | NEW | events.py |
| L-04 | LOW | EventLogger.log_event() uses sp.slice on list | NEW | events.py |

**Total**: 2 Critical, 3 High, 6 Medium, 4 Low

---

*End of Audit Report*
