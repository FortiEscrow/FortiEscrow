# API Reference

## SimpleEscrow

### Constructor

```python
SimpleEscrow(depositor, beneficiary, amount, timeout_seconds)
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| depositor | address | Funds the escrow and controls release/refund |
| beneficiary | address | Receives funds on release |
| amount | nat | Escrow amount in mutez |
| timeout_seconds | nat | Seconds until force_refund available |

#### Validation

| Constraint | Error |
|------------|-------|
| depositor != beneficiary | ESCROW_SAME_PARTY |
| amount > 0 | ESCROW_ZERO_AMOUNT |
| timeout_seconds >= 3600 | ESCROW_TIMEOUT_TOO_SHORT |
| timeout_seconds <= 31536000 | ESCROW_TIMEOUT_TOO_LONG |

### Entrypoints

#### fund()

Deposits exact escrow amount into contract.

**Signature**: `fund()`

**Authorization**: depositor only

**Preconditions**:
- state == INIT
- sp.amount == escrow_amount

**Effects**:
- state := FUNDED
- funded_at := now
- deadline := now + timeout_seconds

**Errors**:
- ESCROW_ALREADY_FUNDED: state != INIT
- ESCROW_NOT_DEPOSITOR: sender != depositor
- ESCROW_AMOUNT_MISMATCH: amount != escrow_amount

---

#### release()

Transfers funds to beneficiary.

**Signature**: `release()`

**Authorization**: depositor only

**Preconditions**:
- state == FUNDED
- now < deadline (strictly before)

**Effects**:
- state := RELEASED
- balance transferred to beneficiary via `_settle()`

**Errors**:
- ESCROW_NOT_FUNDED: state != FUNDED
- ESCROW_NOT_DEPOSITOR: sender != depositor
- ESCROW_DEADLINE_PASSED: now >= deadline

---

#### refund()

Returns funds to depositor.

**Signature**: `refund()`

**Authorization**: depositor only

**Preconditions**:
- state == FUNDED

**Effects**:
- state := REFUNDED
- balance transferred to depositor via `_settle()`

**Errors**:
- ESCROW_NOT_FUNDED: state != FUNDED
- ESCROW_NOT_DEPOSITOR: sender != depositor

---

#### force_refund()

Permissionless recovery at or after timeout.

**Signature**: `force_refund()`

**Authorization**: anyone (at or after timeout)

**Preconditions**:
- state == FUNDED
- now >= deadline (at or after)

**Effects**:
- state := REFUNDED
- balance transferred to depositor via `_settle()`

**Errors**:
- ESCROW_NOT_FUNDED: state != FUNDED
- ESCROW_TIMEOUT_NOT_EXPIRED: now < deadline

---

#### default()

Rejects all direct transfers.

**Signature**: `default()`

**Authorization**: n/a

**Effects**: Always fails

**Errors**:
- ESCROW_DIRECT_TRANSFER_NOT_ALLOWED

### Views

#### get_status()

Returns comprehensive escrow status.

**Signature**: `get_status() -> EscrowStatus`

**Return Type**:
```python
EscrowStatus = {
    state: int,              # 0=INIT, 1=FUNDED, 2=RELEASED, 3=REFUNDED
    state_name: string,      # Human-readable state name
    depositor: address,
    beneficiary: address,
    amount: nat,
    deadline: timestamp,
    is_funded: bool,
    is_terminal: bool,
    can_release: bool,
    can_refund: bool,
    can_force_refund: bool
}
```

---

#### get_parties()

Returns party addresses.

**Signature**: `get_parties() -> Parties`

**Return Type**:
```python
Parties = {
    depositor: address,
    beneficiary: address
}
```

---

#### get_timeline()

Returns timeline information.

**Signature**: `get_timeline() -> Timeline`

**Return Type**:
```python
Timeline = {
    funded_at: timestamp,
    deadline: timestamp,
    timeout_seconds: nat,
    is_expired: bool
}
```

---

## MultiSigEscrow

### Constructor

```python
MultiSigEscrow(depositor, beneficiary, arbiter, amount, timeout_seconds)
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| depositor | address | Funds the escrow |
| beneficiary | address | Receives funds on release |
| arbiter | address | Neutral third party for dispute resolution |
| amount | nat | Escrow amount in mutez |
| timeout_seconds | nat | Seconds until force_refund available |

#### Validation

| Constraint | Error |
|------------|-------|
| All three addresses different | ESCROW_SAME_PARTY |
| amount > 0 | ESCROW_ZERO_AMOUNT |
| timeout_seconds >= 3600 | ESCROW_TIMEOUT_TOO_SHORT |
| timeout_seconds <= 31536000 | ESCROW_TIMEOUT_TOO_LONG |

### Entrypoints

#### fund()

Deposits exact escrow amount and resets voting state.

**Signature**: `fund()`

**Authorization**: depositor only

**Preconditions**:
- state == INIT
- sp.amount == escrow_amount

**Effects**:
- state := FUNDED
- funded_at := now
- deadline := now + timeout_seconds
- All voting state reset (votes map, counters, per-voter locks, consensus flag)

**Errors**:
- ESCROW_ALREADY_FUNDED: state != INIT
- ESCROW_NOT_DEPOSITOR: sender != depositor
- ESCROW_AMOUNT_MISMATCH: amount != escrow_amount

---

#### vote_release()

Cast vote to release funds to beneficiary. If 2+ votes for release, consensus executes automatically.

**Signature**: `vote_release()`

**Authorization**: depositor, beneficiary, or arbiter

**Preconditions**:
- state == FUNDED
- consensus_executed == false
- Sender has not already voted (via any vote entrypoint)

**Effects**:
- Records VOTE_RELEASE for sender
- Increments release_votes counter
- Sets per-voter lock (depositor_voted / beneficiary_voted / arbiter_voted)
- If release_votes >= 2: consensus executes release

**Consensus Execution** (when triggered):
- consensus_executed := true
- state := RELEASED
- All voting state reset
- balance transferred to beneficiary via `_settle()`

**Errors**:
- ESCROW_NOT_FUNDED: state != FUNDED
- CONSENSUS_ALREADY_EXECUTED: consensus already triggered
- ESCROW_UNAUTHORIZED: sender not a party
- DEPOSITOR_ALREADY_VOTED / BENEFICIARY_ALREADY_VOTED / ARBITER_ALREADY_VOTED: per-voter lock

---

#### vote_refund()

Cast vote to refund funds to depositor. If 2+ votes for refund, consensus executes automatically.

**Signature**: `vote_refund()`

**Authorization**: depositor, beneficiary, or arbiter

**Preconditions**:
- state == FUNDED
- consensus_executed == false
- Sender has not already voted (via any vote entrypoint)

**Effects**:
- Records VOTE_REFUND for sender
- Increments refund_votes counter
- Sets per-voter lock (depositor_voted / beneficiary_voted / arbiter_voted)
- If refund_votes >= 2: consensus executes refund

**Consensus Execution** (when triggered):
- consensus_executed := true
- state := REFUNDED
- All voting state reset
- balance transferred to depositor via `_settle()`

**Errors**:
- ESCROW_NOT_FUNDED: state != FUNDED
- CONSENSUS_ALREADY_EXECUTED: consensus already triggered
- ESCROW_UNAUTHORIZED: sender not a party
- DEPOSITOR_ALREADY_VOTED / BENEFICIARY_ALREADY_VOTED / ARBITER_ALREADY_VOTED: per-voter lock

---

#### raise_dispute(reason)

Raise a dispute for arbiter attention. Informational only; does not change voting mechanics.

**Signature**: `raise_dispute(reason: string)`

**Authorization**: depositor or beneficiary (not arbiter)

**Preconditions**:
- state == FUNDED

**Effects**:
- dispute_state := DISPUTE_PENDING
- dispute_reason := reason

**Errors**:
- ESCROW_NOT_FUNDED: state != FUNDED
- ESCROW_UNAUTHORIZED: sender is arbiter or non-party

---

#### force_refund()

Permissionless recovery at or after timeout. Bypasses voting entirely.

**Signature**: `force_refund()`

**Authorization**: anyone (at or after timeout)

**Preconditions**:
- state == FUNDED
- now >= deadline (at or after)

**Effects**:
- state := REFUNDED
- All voting state reset
- balance transferred to depositor via `_settle()`

**Errors**:
- ESCROW_NOT_FUNDED: state != FUNDED
- ESCROW_TIMEOUT_NOT_EXPIRED: now < deadline

### Views

#### get_status()

Returns comprehensive escrow status including voting state.

**Signature**: `get_status() -> MultiSigStatus`

**Return Type**:
```python
MultiSigStatus = {
    state: int,
    state_name: string,
    depositor: address,
    beneficiary: address,
    arbiter: address,
    amount: nat,
    deadline: timestamp,
    is_funded: bool,
    is_terminal: bool,
    release_votes: nat,
    refund_votes: nat,
    dispute_state: int,
    is_timeout_expired: bool
}
```

---

#### get_votes()

Returns current voting status for all parties.

**Signature**: `get_votes() -> VoteStatus`

**Return Type**:
```python
VoteStatus = {
    depositor_vote: int,       # -1 = not voted, 0 = RELEASE, 1 = REFUND
    beneficiary_vote: int,
    arbiter_vote: int,
    release_votes: nat,
    refund_votes: nat,
    votes_needed: nat          # Always 2
}
```

---

#### get_parties()

Returns all party addresses.

**Signature**: `get_parties() -> Parties`

**Return Type**:
```python
Parties = {
    depositor: address,
    beneficiary: address,
    arbiter: address
}
```

---

## Error Codes

### State Errors

| Code | Description |
|------|-------------|
| ESCROW_INVALID_STATE | Invalid state for operation |
| ESCROW_ALREADY_FUNDED | Contract already funded |
| ESCROW_NOT_FUNDED | Contract not in FUNDED state |
| ESCROW_TERMINAL_STATE | Contract in terminal state |

### Authorization Errors

| Code | Description |
|------|-------------|
| ESCROW_UNAUTHORIZED | Sender not authorized |
| ESCROW_NOT_DEPOSITOR | Sender is not depositor |
| ESCROW_NOT_BENEFICIARY | Sender is not beneficiary |

### Amount Errors

| Code | Description |
|------|-------------|
| ESCROW_ZERO_AMOUNT | Amount cannot be zero |
| ESCROW_AMOUNT_MISMATCH | Transferred amount != escrow_amount |
| ESCROW_INSUFFICIENT_BALANCE | Insufficient contract balance |

### Timeout Errors

| Code | Description |
|------|-------------|
| ESCROW_TIMEOUT_TOO_SHORT | Timeout < 1 hour |
| ESCROW_TIMEOUT_TOO_LONG | Timeout > 1 year |
| ESCROW_TIMEOUT_NOT_EXPIRED | Deadline not yet reached |
| ESCROW_DEADLINE_PASSED | Deadline already reached |

### Parameter Errors

| Code | Description |
|------|-------------|
| ESCROW_INVALID_PARAMS | Invalid parameter value |
| ESCROW_SAME_PARTY | Two or more party addresses are identical |
| ESCROW_INVALID_ADDRESS | Invalid address format |

### Transfer Errors

| Code | Description |
|------|-------------|
| ESCROW_DIRECT_TRANSFER_NOT_ALLOWED | Direct transfer rejected |

### MultiSig Voting Errors

| Code | Description |
|------|-------------|
| CONSENSUS_ALREADY_EXECUTED | Consensus already triggered for this escrow |
| INVALID_STATE_FOR_CONSENSUS | Contract not in FUNDED state during consensus check |
| VOTE_CONSENSUS_CONFLICT | Both release and refund have 2+ votes (invariant violation) |
| DEPOSITOR_ALREADY_VOTED | Depositor has already cast a vote |
| BENEFICIARY_ALREADY_VOTED | Beneficiary has already cast a vote |
| ARBITER_ALREADY_VOTED | Arbiter has already cast a vote |
| VOTING_COUNT_MISMATCH_RELEASE | Release vote counter diverged from actual votes |
| VOTING_COUNT_MISMATCH_REFUND | Refund vote counter diverged from actual votes |
| VOTING_LOCK_INCONSISTENCY_* | Per-voter lock flag inconsistent with votes map |
| CONSENSUS_AGREEMENT_INVALID | Manual recount detected impossible consensus state |
| INVALID_PRECONDITION_STATE | State precondition check failed in settlement |

## Type Definitions

### EscrowConfig

Configuration for factory deployment.

```python
EscrowConfig = {
    depositor: address,
    beneficiary: address,
    amount: nat,
    timeout_seconds: nat
}
```

### State Constants

```python
STATE_INIT = 0
STATE_FUNDED = 1
STATE_RELEASED = 2
STATE_REFUNDED = 3
```

### MultiSig Vote Types

```python
VOTE_RELEASE = 0
VOTE_REFUND = 1
```

### Dispute States

```python
DISPUTE_NONE = 0       # No dispute active
DISPUTE_PENDING = 1    # Dispute raised, awaiting resolution
DISPUTE_RESOLVED = 2   # Dispute resolved by arbiter
```

### Timeout Constants

```python
MIN_TIMEOUT_SECONDS = 3600        # 1 hour
MAX_TIMEOUT_SECONDS = 31536000    # 1 year
```

## Deadline Semantics

Both SimpleEscrow and MultiSigEscrow use identical deadline boundary semantics:

```
Timeline:      [fund_at] ←── timeout_seconds ──→ [deadline]

release window:       [fund_at, deadline)    ← strictly before deadline
force_refund window:              [deadline, ∞)  ← from deadline onward

At now == deadline:
  release():       now < deadline? NO  → FAILS
  force_refund():  now >= deadline? YES → SUCCEEDS
```

No gap, no overlap. The deadline is the exact boundary between the release window and the recovery window.

## Usage Examples

### Create and Fund SimpleEscrow

```python
# Deploy
escrow = SimpleEscrow(
    depositor=alice,
    beneficiary=bob,
    amount=sp.nat(5_000_000),
    timeout_seconds=sp.nat(604800)
)

# Fund
escrow.fund().run(
    sender=alice,
    amount=sp.mutez(5_000_000)
)
```

### Release Funds (SimpleEscrow)

```python
escrow.release().run(sender=alice)
```

### Create and Use MultiSigEscrow

```python
# Deploy
escrow = MultiSigEscrow(
    depositor=alice,
    beneficiary=bob,
    arbiter=charlie,
    amount=sp.nat(10_000_000),
    timeout_seconds=sp.nat(604800)
)

# Fund
escrow.fund().run(sender=alice, amount=sp.mutez(10_000_000))

# Depositor and beneficiary agree to release
escrow.vote_release().run(sender=alice)
escrow.vote_release().run(sender=bob)  # 2-of-3 reached: auto-releases

# OR: Depositor and arbiter agree to refund
escrow.vote_refund().run(sender=alice)
escrow.vote_refund().run(sender=charlie)  # 2-of-3 reached: auto-refunds
```

### Force Refund (After Timeout)

```python
# Anyone can call at or after deadline
escrow.force_refund().run(sender=anyone)
```

### Query Status

```python
status = escrow.get_status()
```
