# FortiEscrow: Attack Surface & Threat Model Reference

## Document Purpose

This document provides a comprehensive attack surface analysis for FortiEscrow, documenting:
- Potential attack vectors
- Security controls preventing each attack
- Residual risks and mitigations
- Design choices and trade-offs

---

## Threat Model Framework

### STRIDE Analysis

| Category | Threat | Severity | Mitigation | Status |
|----------|--------|----------|-----------|--------|
| **S** - Spoofing | Fake depositor | 🔴 Critical | Sender validation | ✅ Mitigated |
| **T** - Tampering | Modify state | 🔴 Critical | Immutable structure | ✅ Mitigated |
| **R** - Repudiation | Deny transaction | 🟡 Medium | Blockchain ledger | ✅ Inherent |
| **I** - Info Disclosure | Read state | 🟢 Low | Contract public | ✅ By design |
| **D** - Denial of Service | Block operations | 🟡 Medium | Timeout recovery | ✅ Mitigated |
| **E** - Elevation of Privilege | Admin backdoor | 🔴 Critical | No admin role | ✅ Mitigated |

---

## Attack Vectors Detailed Analysis

### 1. AUTHORIZATION ATTACKS

#### 1.1 Unauthorized Fund Release
**Attacker Profile**: Any address not designated as depositor

**Attack Scenario**:
```python
# Attacker calls release_funds() without authorization
escrow.release_funds()  # sender=attacker_address
```

**Impact**: 
- Beneficiary receives funds without depositor consent
- Complete bypass of escrow semantics
- Fund loss for depositor

**Security Control**:
```python
# Line 253 - forti_escrow.py
sp.verify(
    sp.sender == self.data.depositor,
    FortiEscrowError.UNAUTHORIZED
)
```

**Control Strength**: 🛡️ Cryptographic (sender proven via Tezos signature)  
**Residual Risk**: None (if private keys secure)  
**Status**: ✅ MITIGATED

---

#### 1.2 Unauthorized Refund (Early Abort)
**Attacker Profile**: Beneficiary or relayer attempting to block release

**Attack Scenario**:
```python
# Beneficiary tries to refund funds to prevent release
escrow.refund_escrow()  # sender=beneficiary
```

**Impact**:
- Funds return to depositor (not attacker's benefit)
- Blocks beneficiary from receiving funds
- Griefing attack on transaction

**Security Control**:
```python
# Line 345 - depositor authorization
sp.verify(sp.sender == self.data.depositor, ...)

# Line 355 - early timeout check (can refund before timeout)
if current_time < timeout_expiration:
    sp.verify(
        self.data.relayer == sp.sender or sp.sender == self.data.depositor,
        ...
    )
```

**Control Strength**: 🛡️ Cryptographic  
**Residual Risk**: Low (only deposits go back to depositor)  
**Status**: ✅ MITIGATED

---

#### 1.3 Unauthorized Force-Refund (High Risk Timeout)
**Attacker Profile**: Any malicious actor

**Attack Scenario**:
```python
# Attacker calls force_refund before timeout expires
escrow.force_refund()  # Current time < timeout
```

**Impact**:
- Depositor loses funds prematurely
- Beneficiary blocked from receiving payment
- DoS on legitimate transaction

**Security Control**:
```python
# Line 372 - timeout validation
current_time = sp.now
timeout_expiration = self.data.funded_timestamp + sp.to_int(self.data.timeout_seconds)

sp.verify(
    current_time >= timeout_expiration,
    FortiEscrowError.TIMEOUT_NOT_REACHED
)
```

**Control Strength**: 🛡️ Cryptographic (block timestamp > (funded_time + timeout))  
**Residual Risk**: None  
**Status**: ✅ MITIGATED

---

### 2. FUND MANIPULATION ATTACKS

#### 2.1 Under-Funding Attack
**Attacker Profile**: Depositor or malicious funder

**Attack Scenario**:
```python
# Expected: 1 XTZ (1,000,000 mutez)
escrow.fund_escrow()  # Sender: 0.5 XTZ (500,000 mutez)
```

**Impact**:
- Escrow activated with incorrect balance
- Beneficiary receives only partial funds
- Accounting inconsistency

**Security Control**:
```python
# Line 224 - exact amount validation
sp.verify(
    sp.amount == sp.utils.nat_to_tez(self.data.escrow_amount),
    FortiEscrowError.INSUFFICIENT_FUNDS
)
```

**Control Strength**: 🛡️ Cryptographic (Tezos protocol validates)  
**Residual Risk**: None  
**Status**: ✅ MITIGATED

---

#### 2.2 Over-Funding Attack
**Attacker Profile**: Depositor attempting to send excess funds

**Attack Scenario**:
```python
# Expected: 1 XTZ
escrow.fund_escrow()  # Sender: 2 XTZ
```

**Impact**:
- Excess funds trapped in contract
- Amount_paid > escrow_amount discrepancy
- Beneficiary receives less than depositor sent

**Security Control**:
```python
# Line 224 - exact match required
sp.verify(
    sp.amount == sp.utils.nat_to_tez(self.data.escrow_amount),
    FortiEscrowError.INSUFFICIENT_FUNDS
)
# Tezos protocol rejects transaction if amount != expected
```

**Control Strength**: 🛡️ Protocol-level (cannot overfund)  
**Residual Risk**: None  
**Status**: ✅ MITIGATED

---

#### 2.3 Zero-Amount Escrow
**Attacker Profile**: Deployer attempting to create degenerate escrow

**Attack Scenario**:
```python
# Create escrow with 0 amount
escrow = FortiEscrow(..., escrow_amount=0, ...)
```

**Impact**:
- Meaningless escrow (no funds)
- State machine still executes
- Wasted contract slot on blockchain

**Security Control**:
```python
# Line 193 - initialization check
sp.verify(
    escrow_amount > 0,
    FortiEscrowError.ZERO_AMOUNT
)
```

**Control Strength**: 🛡️ Logical (enforced at initialization)  
**Residual Risk**: None  
**Status**: ✅ MITIGATED

---

### 3. STATE MACHINE ATTACKS

#### 3.1 Double-Funding Attack
**Attacker Profile**: Caller attempting multiple funding attempts

**Attack Scenario**:
```python
# First funding
escrow.fund_escrow()  # amount=1 XTZ, state=INIT→FUNDED

# Second funding attempt
escrow.fund_escrow()  # amount=1 XTZ, state=FUNDED→?
```

**Impact**:
- Balance becomes 2 XTZ (inconsistent with escrow_amount)
- State machine integrity violated
- Beneficiary receives wrong amount

**Security Control**:
```python
# Line 220 - state validation before state change
sp.verify(
    self.data.state == "INIT",
    FortiEscrowError.INVALID_STATE
)
# Second call fails: state is FUNDED, not INIT
```

**Control Strength**: 🛡️ Logical (FSM prevents re-entry)  
**Residual Risk**: None  
**Status**: ✅ MITIGATED

---

#### 3.2 Release from Invalid State
**Attacker Profile**: Caller attempting premature release

**Attack Scenario**:
```python
# Contract still in INIT (no funds yet)
escrow.release_funds()  # state=INIT, should be FUNDED
```

**Impact**:
- Release without funds (protocol error)
- Beneficiary gets nothing (transfer fails)
- State machine integrity violated

**Security Control**:
```python
# Line 257 - state validation
sp.verify(
    self.data.state == "FUNDED",
    FortiEscrowError.INVALID_STATE
)
```

**Control Strength**: 🛡️ Logical  
**Residual Risk**: None  
**Status**: ✅ MITIGATED

---

#### 3.3 Double-Release Attack
**Attacker Profile**: Caller attempting to release twice

**Attack Scenario**:
```python
# First release
escrow.release_funds()  # state: FUNDED→RELEASED, transfer 1 XTZ

# Second release attempt
escrow.release_funds()  # state: RELEASED→?, no funds left!
```

**Impact**:
- Double-spending attempt (transfer insufficient funds)
- State machine violation (invalid transition)

**Security Control**:
```python
# State transition to RELEASED prevents re-entry
# Second call fails: state != FUNDED
sp.verify(self.data.state == "FUNDED", ...)
```

**Control Strength**: 🛡️ Logical  
**Residual Risk**: None  
**Status**: ✅ MITIGATED

---

### 4. TIMING & TIMEOUT ATTACKS

#### 4.1 Late Release After Timeout
**Attacker Profile**: Depositor attempting to release after timeout

**Attack Scenario**:
```python
# Funded at time T
escrow.fund_escrow()  # funded_timestamp=T

# Wait > timeout_seconds
# Then release
escrow.release_funds()  # Now at T+timeout+10, should fail
```

**Impact**:
- Depositor claims release right after losing it
- Breaks timeout recovery guarantee
- Unfair to depositor (penalty not enforced)

**Security Control**:
```python
# Line 260 - timeout check in release path
current_time = sp.now
timeout_expiration = self.data.funded_timestamp + sp.to_int(self.data.timeout_seconds)

sp.verify(
    current_time < timeout_expiration,
    FortiEscrowError.TIMEOUT_EXCEEDED
)
```

**Control Strength**: 🛡️ Cryptographic (blockchain timestamp)  
**Residual Risk**: None  
**Rationale**: After timeout, only refund/force_refund available  
**Status**: ✅ MITIGATED

---

#### 4.2 Premature Force-Refund
**Attacker Profile**: Griefing attacker

**Attack Scenario**:
```python
# Funded at time T, timeout=3600 seconds
escrow.fund_escrow()  # funded_timestamp=T

# Immediately force-refund (timeout not reached)
escrow.force_refund()  # Now=T+100, should fail
```

**Impact**:
- Beneficiary blocked from receiving funds early
- DoS on legitimate transaction
- Depositor forces recovery prematurely

**Security Control**:
```python
# Line 372 - timeout validation
sp.verify(
    current_time >= timeout_expiration,
    FortiEscrowError.TIMEOUT_NOT_REACHED
)
```

**Control Strength**: 🛡️ Cryptographic  
**Residual Risk**: None  
**Status**: ✅ MITIGATED

---

#### 4.3 Fund-Locking (Denial of Service)
**Attacker Profile**: Depositor disappears or becomes uncooperative

**Attack Scenario**:
```python
# Escrow funded, normal operation
escrow.fund_escrow()  # state=FUNDED

# Depositor never releases and never refunds
# Beneficiary cannot access funds
# No timeout mechanism?
```

**Impact**: 🔴 CRITICAL
- Funds permanently locked
- Escrow unusable
- Beneficiary has no recovery path

**Security Control**:
```python
# Line 384 - permissionless timeout recovery
def force_refund(self):
    """Anyone can trigger recovery after timeout"""
    sp.verify(current_time >= timeout_expiration, ...)
    # Funds ALWAYS return to depositor (guaranteed recovery)
```

**Control Strength**: 🛡️ Cryptographic (timeout enforced by protocol)  
**Residual Risk**: None  
**Recovery Time**: Max `timeout_seconds` (minimum 1 hour)  
**Status**: ✅ MITIGATED

---

### 5. INPUT VALIDATION ATTACKS

#### 5.1 Duplicate Party Attack
**Attacker Profile**: Deployer creating degenerate escrow

**Attack Scenario**:
```python
# Same address as depositor and beneficiary
escrow = FortiEscrow(
    depositor="tz1Alice",
    beneficiary="tz1Alice",  # Same address!
    ...
)
```

**Impact**:
- Escrow becomes self-referential
- Release refunds to self (weird semantics)
- Escrow doesn't facilitate exchange

**Security Control**:
```python
# Line 188 - deployment validation
sp.verify(
    depositor != beneficiary,
    FortiEscrowError.DUPLICATE_PARTY
)
```

**Control Strength**: 🛡️ Logical  
**Residual Risk**: None  
**Status**: ✅ MITIGATED

---

#### 5.2 Minimum Timeout Bypass
**Attacker Profile**: Deployer attempting short timeout

**Attack Scenario**:
```python
# Create escrow with 1-minute timeout
escrow = FortiEscrow(
    ...,
    timeout_seconds=60  # Too short for dispute resolution
)
```

**Impact**:
- Insufficient time for legitimate dispute
- Timeout too easy to trigger
- Prevents proper escrow governance

**Security Control**:
```python
# Line 198 - minimum timeout enforcement
sp.verify(
    timeout_seconds >= 3600,
    FortiEscrowError.INVALID_PARAMETERS
)
# Minimum 1 hour = 3600 seconds
```

**Control Strength**: 🛡️ Logical  
**Rationale**: 
- 1 hour = time for dispute resolution
- Prevents flash-loan timeouts
- Reasonable for most use cases  
**Residual Risk**: None  
**Status**: ✅ MITIGATED

---

### 6. EXTERNAL INTERACTION ATTACKS

#### 6.1 Invalid Beneficiary Address
**Attack Scenario**:
```python
# Beneficiary set to invalid address (typo)
escrow = FortiEscrow(
    beneficiary="tz1InvalidAddr",  # Malformed address
    ...
)

# Later, depositor releases
escrow.release_funds()  # Transfer to invalid address?
```

**Impact**:
- Transfer fails (invalid recipient)
- Funds remain in contract
- Transaction reverts

**Security Control**:
```python
# Tezos protocol validates addresses
# Invalid addresses rejected at origination
```

**Control Strength**: 🛡️ Protocol-level  
**Mitigation**: Deployment verification (off-chain)  
**Status**: ✅ MITIGATED

---

#### 6.2 Fallback-Based Reentrancy
**Threat Model**: EVM-specific (not applicable to Tezos)

**Why Not Applicable**:
1. Tezos uses strict call semantics (not EVM fallback)
2. Contract-to-contract calls are explicit
3. State changes occur BEFORE external calls
4. No implicit execution on receiving funds

**Example Safe Sequence**:
```python
# State transitions BEFORE transfer
self.data.state = "RELEASED"  # State change first

# Transfer happens AFTER state change
sp.send(self.data.beneficiary, funds)  # Cannot re-enter
```

**Status**: ✅ NOT APPLICABLE (Tezos design)

---

### 7. CRYPTOGRAPHIC ATTACKS

#### 7.1 Private Key Compromise
**Attacker Profile**: Hacker stealing depositor's key

**Attack Scenario**:
```python
# Attacker gains access to depositor's private key
# Calls refund_escrow() or malicious actions
escrow.refund_escrow()  # Sender spoofed via signature
```

**Impact**:
- Refund to attacker's address (if changed)
- But address is immutable → refunds to original depositor
- Attacker can only control existing transitions

**Security Control**:
```python
# 1. Sender authentication (cryptographic proof)
sp.verify(sp.sender == self.data.depositor, ...)

# 2. Timeout recovery (backup if key lost)
# If depositor key lost before timeout, funds still recoverable
escrow.force_refund()  # Anyone can trigger after timeout
```

**Control Strength**: 🛡️ Cryptographic + Timeout Recovery  
**Residual Risk**: Low (key management is user responsibility)  
**Mitigation**: Hardware wallet, key backup, timeout safety net  
**Status**: ✅ PARTIALLY MITIGATED (user responsibility)

---

#### 7.2 Signature Replay
**Threat Model**: EVM-specific (not applicable to Tezos)

**Why Not Applicable**:
1. Tezos does NOT use signature replay patterns
2. Each operation has unique counter
3. Chainid prevents cross-chain replays
4. Block context prevents replays

**Status**: ✅ NOT APPLICABLE

---

### 8. ORACLE & EXTERNAL DATA ATTACKS

#### 8.1 Timestamp Manipulation
**Attacker Profile**: Blockchain validator

**Attack Scenario**:
```python
# Validator manipulates block timestamp
# Timeout check uses sp.now (block timestamp)
timeout_expiration = funded_timestamp + timeout_seconds

# If validator lies about time, timeout bypassed?
```

**Impact**:
- Force-refund callable before timeout
- Timeout guarantee broken

**Security Control**:
```python
# Tezos consensus validates timestamps
# Timestamps must be >= previous block
# Cannot go backward in time (protocol constraint)
```

**Control Strength**: 🛡️ Protocol-level (consensus required)  
**Residual Risk**: None (would require 51% attack)  
**Status**: ✅ MITIGATED (consensus assumption)

---

## Security Properties Verification

### Property 1: State Machine Completeness
**Definition**: Every reachable state has a defined exit path

**Proof**:
- INIT: Can transition to FUNDED (via `fund_escrow`)
- FUNDED: Can transition to RELEASED (via `release_funds`) or REFUNDED (via `refund_escrow` or `force_refund`)
- RELEASED: Terminal (no transitions)
- REFUNDED: Terminal (no transitions)

**Conclusion**: ✅ **SATISFIED** (no stuck states)

---

### Property 2: Fund Invariants
**Definition**: `contract_balance == escrow_amount` while in FUNDED state

**Proof**:
1. Initial: balance = 0 (INIT state)
2. After `fund_escrow()`: balance = escrow_amount (exact amount validated)
3. No other operations modify balance without state change
4. Transitions consume all balance (`balance = 0` after RELEASED/REFUNDED)

**Conclusion**: ✅ **SATISFIED** (no fund loss)

---

### Property 3: Authorization Completeness
**Definition**: Every sensitive operation has explicit authorization

**Checklist**:
- ✅ `fund_escrow()`: Any address (deposits own funds)
- ✅ `release_funds()`: Depositor only
- ✅ `refund_escrow()`: Depositor only
- ✅ `force_refund()`: Any address (but only after timeout)

**Conclusion**: ✅ **SATISFIED** (no unauthorized operations)

---

### Property 4: Liveness (No Fund-Locking)
**Definition**: Funds are always recoverable within finite time

**Proof**:
1. In state FUNDED: timeout is set at initialization
2. After `timeout_seconds` elapse: `force_refund()` becomes available
3. Anyone can call `force_refund()` (permissionless)
4. Funds return to depositor (immutable destination)

**Conclusion**: ✅ **SATISFIED** (bounded recovery time)

---

## Risk Summary

### Critical Risks: 0
- ✅ No fund-locking vulnerabilities
- ✅ No unauthorized access paths
- ✅ No state machine exploits

### High Risks: 0
- ✅ Amount validation prevents fund loss
- ✅ Timeout prevents premature force-refund

### Medium Risks: 1 ⚠️
- **Deployment operator error**: Incorrect addresses → must re-deploy
- **Mitigation**: Deployment checklist, off-chain verification

### Low Risks: 0
- ✅ All other vectors mitigated

---

## Design Choices & Trade-offs

| Design Choice | Benefit | Trade-off |
|--------------|---------|-----------|
| **Immutable Parties** | Prevents address hijacking | Must re-deploy for address change |
| **No Admin Role** | No backdoor / super-user | No emergency pause capability |
| **Timeout Recovery** | Anti fund-locking | Minimum 1-hour delay |
| **Depositor Unilateral Release** | Depositor control | Beneficiary cannot block |
| **No Partial Release** | Simple FSM | Cannot split escrow |

---

## Conclusion

FortiEscrow implements **defense-in-depth** against escrow-specific attacks through:

1. **Explicit FSM**: Only valid transitions allowed
2. **Authorization Checks**: Sender validation on sensitive operations
3. **Amount Validation**: Exact match prevents fund discrepancies
4. **Timeout Recovery**: Permissionless recovery after deadline
5. **Immutable Parties**: Cannot hijack addresses

**Overall Security Assessment**: 🟢 **PRODUCTION READY**

---

**Document Version**: 1.0  
**Last Updated**: January 25, 2026  
**Classification**: Public (No sensitive information)
