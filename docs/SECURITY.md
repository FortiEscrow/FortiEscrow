# Security

This document describes the **FortiEscrow threat model, semantic guarantees, and security architecture**.
FortiEscrow is a **smart contract framework**, not an application.
Its purpose is to **eliminate high-critical semantic escrow failures by design**, not to patch individual exploits.

---

## Trust Model

### Trusted Components

| Component | Assumption |
|-----------|------------|
| Tezos blockchain | Cryptographic consensus and state execution are secure |
| SmartPy compiler | Generates correct and deterministic Michelson |
| Tezos account signature schemes | Ed25519, Secp256k1, and P256 signatures are computationally infeasible to forge |

---

### Untrusted Parties

| Party | Threat |
|-------|--------|
| Depositor | May disappear or refuse to release funds |
| Beneficiary | May refuse delivery or attempt renegotiation |
| Arbiter (MultiSig) | May delay resolution or collude with a party |
| Third parties | May attempt to intercept or trigger unauthorized operations |
| Validators | Cannot be trusted for precise timestamp accuracy |

---

### Layer Assumptions

FortiEscrow assumes:
- Monotonically increasing block timestamps within protocol bounds
- No reliance on precise timing, only eventual timeout expiry
- Correct execution of Tezos L1 and Etherlink rollup state transitions
- Escrow semantics are enforced identically across layers via adapters

---

### Deliberate Omissions

| Feature | Rationale |
|---------|-----------|
| Admin/owner role | Admin keys introduce unilateral override risks |
| Emergency pause | Pausing can be abused to lock funds |
| Oracle integration | Eliminates oracle manipulation vectors |
| Upgradability | Immutable code prevents proxy and governance attacks |

---

## Security Non-Goals

FortiEscrow explicitly does **not** attempt to:
- Resolve off-chain disputes
- Enforce delivery of goods or services
- Judge fairness of outcomes
- Recover funds after terminal settlement
- Provide arbitration or governance mechanisms beyond 2-of-3 voting

---

## Semantic Guarantees

FortiEscrow guarantees that:
- Every escrow reaches a terminal state
- No funds can remain permanently locked
- No privileged party can override settlement rules
- Escrow behavior is independent of application context
- Incorrect escrow implementations are made impossible by design
- No single party can unilaterally move funds (MultiSig)
- Settlement uses `sp.balance` (not `escrow_amount`), preventing residual fund lockup

---

## Threat Catalog

### T1: Permanent Fund Lock

**Severity**: Critical

**Attack**: Funds become permanently inaccessible.

**Mitigations**:
1. Early refund: depositor can call `refund()` before settlement (SimpleEscrow)
2. Timeout recovery: `force_refund()` is permissionless at or after deadline
3. No admin: no party can extend deadlines or freeze execution
4. Deadline immutability: set once at funding, never modified
5. Settlement via `sp.balance`: transfers ALL contract funds, preventing dust lockup

**Invariants**: #4 (Time Safety), #5 (No Fund-Locking)

---

### T2: Unauthorized Transfer

**Severity**: Critical

**Attack**: Attacker triggers fund transfer without authorization.

**Mitigations**:

SimpleEscrow:
1. `release()` requires `sp.sender == depositor`
2. `refund()` requires `sp.sender == depositor`
3. `force_refund()` requires `now >= deadline`
4. State must be FUNDED for any transfer

MultiSigEscrow:
1. `vote_release()` / `vote_refund()` requires sender to be a party
2. `force_refund()` requires `now >= deadline`
3. Consensus requires 2-of-3 agreement (no single party can settle)
4. Per-voter locks prevent vote manipulation
5. `consensus_executed` flag prevents double settlement

**Invariants**: #1 (Funds Safety), #3 (Authorization)

---

### T3: State Manipulation

**Severity**: Critical

**Attack**: Invalid or skipped state transitions.

**Mitigations**:
1. Every entrypoint validates current state
2. Terminal states have no outgoing transitions
3. State transitions are atomic and validated
4. MultiSig consensus executes state change before transfer (CEI)

**Invariants**: #2 (State Consistency)

---

### T4: Double Spending

**Severity**: Critical

**Attack**: Funds transferred multiple times.

**Mitigations**:
1. State transitions to terminal before transfer (CEI pattern)
2. Repeated calls fail state checks
3. Atomic execution guaranteed by Tezos
4. MultiSig: `consensus_executed` flag prevents re-execution
5. MultiSig: voting state reset on terminal entry

**Invariants**: #1 (Funds Safety), #2 (State Consistency)

---

### T5: Reentrancy

**Severity**: High

**Attack**: Malicious callback during transfer.

**Mitigations**:
1. State changes before `sp.send()` via CEI pattern
2. Reentrant calls fail state checks (state already terminal)
3. No logic executes after `_settle()` transfer
4. Centralized `_settle()` function ensures uniform transfer behavior

**Invariants**: #1 (Funds Safety), #2 (State Consistency)

---

### T6: Time Manipulation

**Severity**: High

**Attack**: Exploiting deadline boundary conditions.

**Mitigations**:
1. Boundary comparison: `now >= deadline` for recovery, `now < deadline` for release
2. No gap, no overlap at deadline boundary
3. Deadline is immutable after funding
4. Timeout bounds enforced: 1 hour - 1 year
5. No reliance on precise timestamp accuracy

**Invariants**: #4 (Time Safety)

**Deadline Boundary Semantics**:
```
release window:       [fund_at, deadline)    ← strictly before deadline
force_refund window:              [deadline, ∞)  ← from deadline onward
At now == deadline: release FAILS, force_refund SUCCEEDS
```

---

### T7: Front-Running

**Severity**: High

**Attack**: Competing transaction execution.

**Mitigations**:
1. Authorization prevents privilege front-running
2. `force_refund()` outcome is caller-independent (funds go to depositor)
3. Operations are idempotent
4. MultiSig: per-voter locks prevent vote front-running

**Invariants**: #3 (Authorization)

---

### T8: Parameter Validation

**Severity**: Medium

**Attack**: Invalid initialization parameters.

**Mitigations**:
1. `depositor != beneficiary` (all parties different for MultiSig)
2. `amount > 0`
3. Timeout bounds enforced
4. Exact amount matching on `fund()`

---

### T9: Denial of Service

**Severity**: Medium

**Attack**: Preventing legitimate operations.

**Mitigations**:
1. Idempotent operations
2. Minimal storage footprint
3. Timeout-based recovery
4. MultiSig: per-voter locks prevent vote flooding

**Invariants**: #4 (Time Safety), #5 (No Fund-Locking)

---

### T10: Insufficient Funding

**Severity**: Medium

**Attack**: Incorrect funding amount.

**Mitigations**:
1. Exact amount enforcement
2. Underfunding rejected
3. Overfunding reverted

---

### T11: Vote Manipulation (MultiSig)

**Severity**: High

**Attack**: Manipulating vote counts or re-voting to change consensus outcome.

**Mitigations**:
1. Per-voter locks: each party can vote exactly once (no vote changes)
2. Vote count verification: `_verify_voting_invariant()` recounts votes from the map before consensus
3. Mutual exclusion assertion: `release_votes >= 2 AND refund_votes >= 2` is impossible
4. `consensus_executed` flag: consensus executes at most once
5. Voting state lifecycle: all voting data reset on terminal state entry
6. Lock consistency checks: per-voter lock flags verified against votes map

**Invariants**: #1 (Funds Safety), #3 (Authorization)

---

### T12: Double Consensus Settlement (MultiSig)

**Severity**: Critical

**Attack**: Consensus executes twice, causing double fund transfer.

**Mitigations**:
1. `consensus_executed` flag set BEFORE execution (prevents re-entry)
2. State check in `_check_consensus()`: must be FUNDED
3. State transition in `_execute_release()` / `_execute_refund()`: moves to terminal before transfer
4. `sp.if_ / sp.else_` structure ensures mutual exclusion of release vs refund
5. Voting state reset on terminal entry clears all vote data

**Invariants**: #1 (Funds Safety), #2 (State Consistency)

---

## Authorization Matrix

### SimpleEscrow

| Operation | INIT | FUNDED (before deadline) | FUNDED (at/after deadline) | RELEASED | REFUNDED |
|-----------|------|--------------------------|----------------------------|----------|----------|
| fund | depositor | - | - | - | - |
| release | - | depositor | - | - | - |
| refund | - | depositor | depositor | - | - |
| force_refund | - | - | anyone | - | - |

### MultiSigEscrow

| Operation | INIT | FUNDED (before deadline) | FUNDED (at/after deadline) | RELEASED | REFUNDED |
|-----------|------|--------------------------|----------------------------|----------|----------|
| fund | depositor | - | - | - | - |
| vote_release | - | any party | any party | - | - |
| vote_refund | - | any party | any party | - | - |
| raise_dispute | - | depositor/beneficiary | depositor/beneficiary | - | - |
| force_refund | - | - | anyone | - | - |

---

## Settlement Architecture

### Centralized Settlement (`_settle()`)

Both SimpleEscrow and MultiSigEscrow route all fund transfers through `_settle(recipient)`:

```python
def _settle(self, recipient):
    sp.send(recipient, sp.balance)
```

Properties:
- Uses `sp.balance` (not `escrow_amount`): transfers ALL contract funds
- Prevents residual fund lockup from extra XTZ
- Single point of control for security audit
- Caller must change state to terminal BEFORE calling `_settle()` (CEI)

### CEI Pattern Enforcement

All settlement paths follow Checks-Effects-Interactions:

1. **Checks**: Verify state, authorization, consensus
2. **Effects**: Transition state to terminal, reset voting state
3. **Interactions**: Transfer funds via `_settle()`

---

## Code Patterns

### State Verification

```python
def _require_state(self, expected_state, error_msg):
    sp.verify(self.data.state == expected_state, error_msg)
```

### Sender Verification

```python
def _require_sender(self, expected, error_msg):
    sp.verify(sp.sender == expected, error_msg)
```

### MultiSig Party Verification

```python
def _require_party(self):
    sp.verify(
        (sp.sender == self.data.depositor) |
        (sp.sender == self.data.beneficiary) |
        (sp.sender == self.data.arbiter),
        EscrowError.UNAUTHORIZED
    )
```

### Per-Voter Lock Pattern (MultiSig)

```python
with sp.if_(voter == self.data.depositor):
    sp.verify(~self.data.depositor_voted, "DEPOSITOR_ALREADY_VOTED")
    self.data.depositor_voted = True
```
