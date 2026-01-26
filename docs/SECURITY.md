# Security

This document describes the FortiEscrow threat model and security architecture.

## Trust Model

### Trusted Components

| Component | Assumption |
|-----------|------------|
| Tezos blockchain | Cryptographic consensus is secure |
| SmartPy compiler | Generates correct Michelson |
| ECDSA signatures | Computationally infeasible to forge |

### Untrusted Parties

| Party | Threat |
|-------|--------|
| Depositor | May disappear, refuse to release |
| Beneficiary | May refuse delivery, demand more |
| Third parties | May attempt to intercept funds |
| Validators | Cannot be trusted for exact timing |

### Deliberate Omissions

| Feature | Rationale |
|---------|-----------|
| Admin/owner role | Admin keys are attack vectors |
| Emergency pause | Pausing can be abused to lock funds |
| Oracle integration | Eliminates oracle manipulation vectors |
| Upgradability | Immutable code prevents proxy attacks |

## Threat Catalog

### T1: Permanent Fund Lock

**Severity**: Critical

**Attack**: Funds become permanently inaccessible.

**Mitigations**:
1. Early refund: depositor can call `refund()` at any time
2. Timeout recovery: `force_refund()` is permissionless after deadline
3. No admin: no one can extend deadline or freeze contract
4. Deadline immutability: set once at funding, cannot be modified

**Invariants**: #4 (Time Safety), #5 (No Fund-Locking)

### T2: Unauthorized Transfer

**Severity**: Critical

**Attack**: Attacker triggers fund transfer without authorization.

**Mitigations**:
1. `release()` requires `sp.sender == depositor`
2. `refund()` requires `sp.sender == depositor`
3. `force_refund()` requires `now > deadline`
4. State must be FUNDED for any transfer

**Invariants**: #1 (Funds Safety), #3 (Authorization)

### T3: State Manipulation

**Severity**: Critical

**Attack**: Attacker causes invalid state transition.

**Mitigations**:
1. Every entrypoint verifies current state before modification
2. Terminal states have no outgoing transitions
3. State changes occur atomically with validation

**Invariants**: #2 (State Consistency)

### T4: Double Spending

**Severity**: Critical

**Attack**: Funds transferred multiple times from single escrow.

**Mitigations**:
1. State transitions to terminal before transfer
2. Second call fails state check (not FUNDED)
3. Tezos guarantees atomic execution

**Invariants**: #1 (Funds Safety), #2 (State Consistency)

### T5: Reentrancy

**Severity**: High

**Attack**: Malicious beneficiary contract calls back during transfer.

**Mitigations**:
1. State changes to terminal before `sp.send()`
2. Reentrant call fails: state is no longer FUNDED
3. No code executes after `sp.send()`

**Invariants**: #1 (Funds Safety), #2 (State Consistency)

### T6: Time Manipulation

**Severity**: High

**Attack**: Attacker manipulates deadline checks.

**Mitigations**:
1. `force_refund()` uses strict comparison: `now > deadline`
2. Deadline is immutable after funding
3. Timeout bounds: 1 hour minimum, 1 year maximum
4. Block timestamps protected by consensus

**Invariants**: #4 (Time Safety)

### T7: Front-Running

**Severity**: High

**Attack**: Attacker observes pending transaction and executes competing operation.

**Mitigations**:
1. Authorization checks make privileged operations non-frontrunnable
2. `force_refund()` sends to depositor regardless of caller
3. Operations are idempotent (second call fails)

**Invariants**: #3 (Authorization)

### T8: Parameter Validation

**Severity**: Medium

**Attack**: Invalid parameters cause unexpected behavior.

**Mitigations**:
1. `depositor != beneficiary` enforced at initialization
2. `amount > 0` enforced at initialization
3. Timeout bounds enforced: `[1 hour, 1 year]`
4. Exact amount matching on `fund()`

### T9: Denial of Service

**Severity**: Medium

**Attack**: Attacker prevents legitimate operations.

**Mitigations**:
1. Operations are idempotent (spam is rejected cheaply)
2. Minimal storage (8 fields, no collections)
3. Timeout ensures eventual recovery

**Invariants**: #4 (Time Safety), #5 (No Fund-Locking)

### T10: Insufficient Funding

**Severity**: Medium

**Attack**: Depositor sends incorrect amount.

**Mitigations**:
1. Exact amount matching: `sp.amount == escrow_amount`
2. Underfunding rejected
3. Overfunding rejected (transaction reverted)

## Authorization Matrix

| Operation | INIT | FUNDED (before deadline) | FUNDED (after deadline) | RELEASED | REFUNDED |
|-----------|------|--------------------------|-------------------------|----------|----------|
| fund | depositor | - | - | - | - |
| release | - | depositor | - | - | - |
| refund | - | depositor | depositor | - | - |
| force_refund | - | - | anyone | - | - |

## Code Patterns

### State Verification

```python
def _require_state(self, expected_state, error_msg):
    sp.verify(self.data.state == expected_state, error_msg)
```

### Authorization Check

```python
def _require_sender(self, expected, error_msg):
    sp.verify(sp.sender == expected, error_msg)
```

### Checks-Effects-Interactions

```python
@sp.entry_point
def release(self):
    # CHECKS
    self._require_state(STATE_FUNDED, EscrowError.NOT_FUNDED)
    self._require_sender(self.data.depositor, EscrowError.NOT_DEPOSITOR)
    sp.verify(sp.now <= self.data.deadline, EscrowError.DEADLINE_PASSED)

    # EFFECTS
    self.data.state = STATE_RELEASED

    # INTERACTIONS
    sp.send(self.data.beneficiary, sp.balance)
```

## Audit Checklist

### State Machine

- [ ] All entrypoints verify current state before modification
- [ ] Terminal states have no outgoing transitions
- [ ] Only valid FSM transitions are possible

### Authorization

- [ ] `release()` requires depositor
- [ ] `refund()` requires depositor
- [ ] `force_refund()` requires timeout expiry
- [ ] No admin/owner backdoors

### Funds

- [ ] `sp.send()` only after state is terminal
- [ ] No other transfer mechanisms exist
- [ ] Exact amount matching enforced

### Timing

- [ ] Deadline set once at funding
- [ ] No mechanism to extend deadline
- [ ] Timeout bounds enforced

### Parameters

- [ ] depositor != beneficiary
- [ ] amount > 0
- [ ] timeout within bounds

## Invariant Enforcement Locations

| Invariant | Enforcement | File:Line |
|-----------|-------------|-----------|
| #1 Funds Safety | State change before transfer | escrow_base.py:335-338 |
| #2 State Consistency | `_require_state()` calls | escrow_base.py:207-209 |
| #3 Authorization | `_require_sender()` calls | escrow_base.py:223-225 |
| #4 Time Safety | Timeout bounds + deadline check | escrow_base.py:166-176, 405-408 |
| #5 No Fund-Locking | Multiple exit paths | escrow_base.py:300-414 |

## Reporting Vulnerabilities

Report security vulnerabilities to the repository maintainers. Do not disclose publicly until a fix is available.
