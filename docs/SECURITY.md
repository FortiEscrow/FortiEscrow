# Security

This document describes the **FortiEscrow threat model, semantic guarantees, and security architecture**.
FortiEscrow is a **smart contract framework**, not an application.  
Its purpose is to **eliminate high–critical semantic escrow failures by design**, not to patch individual exploits.

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
- Provide arbitration or governance mechanisms

---

## Semantic Guarantees

FortiEscrow guarantees that:
- Every escrow reaches a terminal state
- No funds can remain permanently locked
- No privileged party can override settlement rules
- Escrow behavior is independent of application context
- Incorrect escrow implementations are made impossible by design

---

## Threat Catalog

### T1: Permanent Fund Lock

**Severity**: Critical

**Attack**: Funds become permanently inaccessible.

**Mitigations**:
1. Early refund: depositor can call `refund()` before settlement  
2. Timeout recovery: `force_refund()` is permissionless after deadline  
3. No admin: no party can extend deadlines or freeze execution  
4. Deadline immutability: set once at funding, never modified  

**Invariants**: #4 (Time Safety), #5 (No Fund-Locking)

**Semantic Note**:  
FortiEscrow intentionally defines escrow semantics where the depositor retains unilateral cancellation rights before settlement. This design choice eliminates permanent fund lock and trust leakage.

---

### T2: Unauthorized Transfer

**Severity**: Critical

**Attack**: Attacker triggers fund transfer without authorization.

**Mitigations**:
1. `release()` requires `sp.sender == depositor`  
2. `refund()` requires `sp.sender == depositor`  
3. `force_refund()` requires `now > deadline`  
4. State must be FUNDED for any transfer  

**Invariants**: #1 (Funds Safety), #3 (Authorization)

---

### T3: State Manipulation

**Severity**: Critical

**Attack**: Invalid or skipped state transitions.

**Mitigations**:
1. Every entrypoint validates current state  
2. Terminal states have no outgoing transitions  
3. State transitions are atomic and validated  

**Invariants**: #2 (State Consistency)

---

### T4: Double Spending

**Severity**: Critical

**Attack**: Funds transferred multiple times.

**Mitigations**:
1. State transitions to terminal before transfer  
2. Repeated calls fail state checks  
3. Atomic execution guaranteed by Tezos  

**Invariants**: #1 (Funds Safety), #2 (State Consistency)

---

### T5: Reentrancy

**Severity**: High

**Attack**: Malicious callback during transfer.

**Mitigations**:
1. State changes before `sp.send()`  
2. Reentrant calls fail state checks  
3. No logic executes after transfer  

**Invariants**: #1 (Funds Safety), #2 (State Consistency)

---

### T6: Time Manipulation

**Severity**: High

**Attack**: Exploiting deadline boundary conditions.

**Mitigations**:
1. Strict comparison: `now > deadline`  
2. Deadline is immutable  
3. Timeout bounds enforced: 1 hour – 1 year  
4. No reliance on precise timestamp accuracy  

**Invariants**: #4 (Time Safety)

---

### T7: Front-Running

**Severity**: High

**Attack**: Competing transaction execution.

**Mitigations**:
1. Authorization prevents privilege front-running  
2. `force_refund()` outcome is caller-independent  
3. Operations are idempotent  

**Invariants**: #3 (Authorization)

---

### T8: Parameter Validation

**Severity**: Medium

**Attack**: Invalid initialization parameters.

**Mitigations**:
1. `depositor != beneficiary`  
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

## Authorization Matrix

| Operation | INIT | FUNDED (before deadline) | FUNDED (after deadline) | RELEASED | REFUNDED |
|-----------|------|--------------------------|-------------------------|----------|----------|
| fund | depositor | – | – | – | – |
| release | – | depositor | – | – | – |
| refund | – | depositor | depositor | – | – |
| force_refund | – | – | anyone | – | – |

---

## Code Patterns

### State Verification

```python
def _require_state(self, expected_state, error_msg):
    sp.verify(self.data.state == expected_state, error_msg)
