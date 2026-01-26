# API Reference

## Constructor

```python
SimpleEscrow(depositor, beneficiary, amount, timeout_seconds)
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| depositor | address | Funds the escrow and controls release/refund |
| beneficiary | address | Receives funds on release |
| amount | nat | Escrow amount in mutez |
| timeout_seconds | nat | Seconds until force_refund available |

### Validation

| Constraint | Error |
|------------|-------|
| depositor != beneficiary | ESCROW_SAME_PARTY |
| amount > 0 | ESCROW_ZERO_AMOUNT |
| timeout_seconds >= 3600 | ESCROW_TIMEOUT_TOO_SHORT |
| timeout_seconds <= 31536000 | ESCROW_TIMEOUT_TOO_LONG |

## Entrypoints

### fund()

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

### release()

Transfers funds to beneficiary.

**Signature**: `release()`

**Authorization**: depositor only

**Preconditions**:
- state == FUNDED
- now <= deadline

**Effects**:
- state := RELEASED
- balance transferred to beneficiary

**Errors**:
- ESCROW_NOT_FUNDED: state != FUNDED
- ESCROW_NOT_DEPOSITOR: sender != depositor
- ESCROW_DEADLINE_PASSED: now > deadline

---

### refund()

Returns funds to depositor.

**Signature**: `refund()`

**Authorization**: depositor only

**Preconditions**:
- state == FUNDED

**Effects**:
- state := REFUNDED
- balance transferred to depositor

**Errors**:
- ESCROW_NOT_FUNDED: state != FUNDED
- ESCROW_NOT_DEPOSITOR: sender != depositor

---

### force_refund()

Permissionless recovery after timeout.

**Signature**: `force_refund()`

**Authorization**: anyone (after timeout)

**Preconditions**:
- state == FUNDED
- now > deadline

**Effects**:
- state := REFUNDED
- balance transferred to depositor

**Errors**:
- ESCROW_NOT_FUNDED: state != FUNDED
- ESCROW_TIMEOUT_NOT_EXPIRED: now <= deadline

---

### default()

Rejects all direct transfers.

**Signature**: `default()`

**Authorization**: n/a

**Effects**: Always fails

**Errors**:
- ESCROW_DIRECT_TRANSFER_NOT_ALLOWED

## Views

### get_status()

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

### get_parties()

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

### get_timeline()

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
| ESCROW_TIMEOUT_NOT_EXPIRED | Deadline not yet passed |
| ESCROW_DEADLINE_PASSED | Deadline already passed |

### Parameter Errors

| Code | Description |
|------|-------------|
| ESCROW_INVALID_PARAMS | Invalid parameter value |
| ESCROW_SAME_PARTY | depositor == beneficiary |
| ESCROW_INVALID_ADDRESS | Invalid address format |

### Transfer Errors

| Code | Description |
|------|-------------|
| ESCROW_DIRECT_TRANSFER_NOT_ALLOWED | Direct transfer rejected |
| ESCROW_BENEFICIARY_TRANSFER_FAILED | Transfer to beneficiary failed |
| ESCROW_DEPOSITOR_TRANSFER_FAILED | Transfer to depositor failed |

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

### Timeout Constants

```python
MIN_TIMEOUT_SECONDS = 3600        # 1 hour
MAX_TIMEOUT_SECONDS = 31536000    # 1 year
```

## Usage Examples

### Create and Fund Escrow

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

### Release Funds

```python
escrow.release().run(sender=alice)
```

### Refund (Depositor)

```python
escrow.refund().run(sender=alice)
```

### Force Refund (After Timeout)

```python
# Anyone can call after deadline
escrow.force_refund().run(sender=anyone)
```

### Query Status

```python
status = escrow.get_status()
if status.can_release:
    escrow.release().run(sender=depositor)
```
