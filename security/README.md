# Security

Security analysis and formal invariants for FortiEscrow.

For a comprehensive overview, see [docs/SECURITY.md](../docs/SECURITY.md).

## Invariants

FortiEscrow enforces five security invariants. These are runtime-enforced constraints, not guidelines.

### Invariant 1: Funds Safety

Funds can only be transferred when the contract reaches a terminal state.

```
∀t: transfer(amount) → state(t) ∈ {RELEASED, REFUNDED}
```

**Enforcement**: State changes to terminal before `sp.send()` in all entrypoints.

**Location**: `escrow_base.py:335-338` (release), `escrow_base.py:371-374` (refund)

### Invariant 2: State Consistency

State transitions follow the FSM exactly. No backward transitions.

```
INIT → FUNDED → {RELEASED | REFUNDED}
```

**Enforcement**: Every entrypoint verifies current state before modification.

**Location**: `escrow_base.py:207-209` (`_require_state`)

### Invariant 3: Authorization

Only authorized parties can execute privileged operations.

| Operation | Authorized Caller |
|-----------|-------------------|
| fund | depositor |
| release | depositor |
| refund | depositor |
| force_refund | anyone (after timeout) |

**Enforcement**: `sp.verify(sp.sender == depositor)` on privileged operations.

**Location**: `escrow_base.py:223-225` (`_require_sender`)

### Invariant 4: Time Safety

Funds are always recoverable after the deadline expires.

```
∀t ≥ deadline: force_refund() succeeds
```

**Enforcement**:
- Deadline = funding_time + timeout_seconds (immutable)
- Timeout bounds: 1 hour ≤ timeout ≤ 1 year

**Location**: `escrow_base.py:166-176`, `escrow_base.py:405-408`

### Invariant 5: No Permanent Fund-Locking

No execution path results in funds being permanently locked.

**Exit paths from FUNDED**:
1. `release()` — depositor transfers to beneficiary
2. `refund()` — depositor reclaims funds
3. `force_refund()` — anyone recovers funds (after deadline)

**Location**: `escrow_base.py:300-414`

## Threat Catalog

| ID | Threat | Severity | Mitigation |
|----|--------|----------|------------|
| T1 | Permanent fund lock | Critical | Timeout recovery, multiple exit paths |
| T2 | Unauthorized transfer | Critical | Sender authentication |
| T3 | State manipulation | Critical | State validation per entrypoint |
| T4 | Double spending | Critical | State transition before transfer |
| T5 | Reentrancy | High | CEI pattern, Tezos call semantics |
| T6 | Time manipulation | High | Strict deadline comparison |
| T7 | Front-running | High | Authorization + idempotency |
| T8 | Parameter validation | Medium | Constructor validation |
| T9 | Denial of service | Medium | Idempotent operations |
| T10 | Insufficient funding | Medium | Exact amount matching |

## Authorization Matrix

| Operation | INIT | FUNDED (pre-deadline) | FUNDED (post-deadline) | Terminal |
|-----------|------|-----------------------|------------------------|----------|
| fund | depositor | - | - | - |
| release | - | depositor | - | - |
| refund | - | depositor | depositor | - |
| force_refund | - | - | anyone | - |

## Checks-Effects-Interactions Pattern

All entrypoints follow this order:

```python
@sp.entry_point
def release(self):
    # 1. CHECKS
    self._require_funded()
    self._require_sender(self.data.depositor, ...)
    sp.verify(sp.now <= self.data.deadline, ...)

    # 2. EFFECTS
    self.data.state = STATE_RELEASED

    # 3. INTERACTIONS
    sp.send(self.data.beneficiary, sp.balance)
```

## Audit Checklist

### State Machine
- [ ] All entrypoints verify current state
- [ ] Terminal states have no outgoing transitions
- [ ] Only valid FSM transitions possible

### Authorization
- [ ] `release()` requires depositor
- [ ] `refund()` requires depositor
- [ ] `force_refund()` requires timeout expiry
- [ ] No admin backdoors

### Funds
- [ ] `sp.send()` only after state is terminal
- [ ] No other transfer mechanisms
- [ ] Exact amount matching enforced

### Timing
- [ ] Deadline set once at funding
- [ ] No mechanism to extend deadline
- [ ] Timeout bounds enforced

### Parameters
- [ ] depositor != beneficiary
- [ ] amount > 0
- [ ] timeout within bounds

## Reporting Vulnerabilities

Report security vulnerabilities to repository maintainers privately. Do not disclose publicly until a fix is available.
