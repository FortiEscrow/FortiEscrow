# FortiEscrow: Deployment & Integration Guide

## Quick Start

### 1. Installation

```bash
# Install SmartPy
pip install smartpy

# Clone FortiEscrow
git clone https://github.com/yourusername/FortiEscrow-Labs.git
cd FortiEscrow-Labs
```

### 2. Compile Contract

```python
import smartpy as sp
from forti_escrow import FortiEscrow

# Define deployment parameters
depositor = sp.address("tz1...")     # Account funding the escrow
beneficiary = sp.address("tz1...")  # Recipient of funds
relayer = sp.address("tz1...")      # Coordinator (optional, non-binding)

escrow_amount = sp.nat(1_000_000)   # Amount in mutez (1 XTZ = 1,000,000 mutez)
timeout_seconds = sp.nat(7 * 24 * 3600)  # 7 days in seconds

# Create contract instance
contract = FortiEscrow(
    depositor=depositor,
    beneficiary=beneficiary,
    relayer=relayer,
    escrow_amount=escrow_amount,
    timeout_seconds=timeout_seconds
)

# Compile to Micheline
sp.add_compilation_target("FortiEscrow", contract)
sp.compile_contract(contract, target_dir="./compiled")
```

### 3. Deploy to Testnet

```bash
# Deploy using Tezos CLI
tezos-client originate contract FortiEscrow \
  transferring 0 from <account> \
  running ./compiled/forti_escrow.tz \
  --init '(Pair (Pair (Pair "tz1..." "tz1...") "tz1...") (Pair <amount> <timeout>))' \
  --burn-cap 1
```

---

## State Machine Overview

```
┌─────────────────────────────────────────────────────────┐
│                    INIT (Initial State)                 │
│               Contract deployed, no funds                │
└──────────────────────┬──────────────────────────────────┘
                       │
                       │ fund_escrow()
                       │ Amount must match escrow_amount
                       │ Caller: anyone
                       ↓
┌─────────────────────────────────────────────────────────┐
│                   FUNDED (Holding State)                │
│        Funds received, awaiting release decision        │
└──────────────────────┬──────────────────────────────────┘
                       │
            ┌──────────┴──────────┐
            │                     │
            │                     │
     ┌──────┴────┐           ┌────┴──────┐
     │           │           │           │
     │ RELEASE   │           │ REFUND    │
     │ TIMEOUT   │           │ PATH      │
     │ NOT YET   │           │           │
     │ EXPIRED   │           │           │
     │           │           │           │
     │release_   │           │refund_    │
     │funds()    │           │escrow()   │
     │Caller:    │           │Caller:    │
     │Depositor  │           │Depositor  │
     │           │           │           │
     └──────┬────┘           └────┬──────┘
            │                     │
            │                     │ Timeout expired?
            │                     │ YES: force_refund()
            │                     │      Caller: anyone
            │                     │
            ↓                     ↓
┌────────────────────┐  ┌────────────────────┐
│    RELEASED        │  │     REFUNDED       │
│   (Terminal)       │  │    (Terminal)      │
│  Funds sent to     │  │  Funds sent to     │
│  beneficiary       │  │  depositor         │
└────────────────────┘  └────────────────────┘
```

---

## Entrypoint Reference

### `fund_escrow()`

**Purpose**: Transition from INIT → FUNDED

**Parameters**:
- `amount`: Must equal `escrow_amount` (in tez)

**Authorization**: Any address

**Preconditions**:
- State must be INIT
- Amount must match exactly
- No previous funding

**Postconditions**:
- State becomes FUNDED
- `funded_timestamp` recorded (for timeout calculation)
- Contract holds funds

**Example**:
```python
escrow.fund_escrow().run(
    amount=sp.utils.nat_to_tez(1_000_000),
    sender=depositor
)
```

---

### `release_funds()`

**Purpose**: Transition from FUNDED → RELEASED

**Parameters**: None

**Authorization**: ONLY depositor

**Preconditions**:
- State must be FUNDED
- Caller must be depositor
- Timeout NOT expired (depositor loses right after timeout)

**Postconditions**:
- State becomes RELEASED
- Funds transferred to beneficiary
- Contract balance = 0

**Example**:
```python
escrow.release_funds().run(
    sender=depositor
)
```

**When to Use**:
- Beneficiary has delivered goods/services
- Depositor is satisfied with transaction
- Both parties agree (depositor's consent sufficient)

---

### `refund_escrow()`

**Purpose**: Transition from FUNDED → REFUNDED (early abort)

**Parameters**: None

**Authorization**: ONLY depositor (or relayer cooperatively)

**Preconditions**:
- State must be FUNDED
- Caller must be depositor
- (Optional): Relayer can cooperate before timeout

**Postconditions**:
- State becomes REFUNDED
- Funds returned to depositor
- Contract balance = 0

**Example**:
```python
escrow.refund_escrow().run(
    sender=depositor
)
```

**When to Use**:
- Depositor changes mind before timeout
- Beneficiary hasn't delivered as expected
- Mutual agreement to abort

---

### `force_refund()`

**Purpose**: Transition from FUNDED → REFUNDED (timeout-driven recovery)

**Parameters**: None

**Authorization**: ANY address (permissionless)

**Preconditions**:
- State must be FUNDED
- Timeout period must have expired
- At least `timeout_seconds` since funding

**Postconditions**:
- State becomes REFUNDED
- Funds returned to depositor
- Contract terminates

**Example**:
```python
# After timeout expires
escrow.force_refund().run(
    sender=anyone_address
)
```

**When to Use**:
- Timeout has passed (anti fund-locking)
- Depositor unavailable
- Beneficiary refuses to sign release
- Relayer has disappeared
- **Result**: Funds always recoverable

---

## View Functions (Read-Only)

### `get_status()`

**Purpose**: Query current escrow state and metadata

**Returns**:
```python
{
  "state": str,              # INIT | FUNDED | RELEASED | REFUNDED
  "depositor": address,
  "beneficiary": address,
  "relayer": address,
  "amount": nat,
  "funded_timestamp": int,
  "timeout_seconds": nat,
  "timeout_expired": bool    # True if force_refund() callable
}
```

**Example**:
```python
status = escrow.get_status()
print(f"State: {status.state}")
print(f"Timeout expired: {status.timeout_expired}")
```

---

### `can_transition(target_state)`

**Purpose**: Check if a specific state transition is currently possible

**Parameters**:
- `target_state`: Target state name ("RELEASED" or "REFUNDED")

**Returns**: Boolean

**Example**:
```python
can_release = escrow.can_transition("RELEASED")
can_refund = escrow.can_transition("REFUNDED")

if can_release:
    print("Can call release_funds() now")
else:
    print("Release not available (timeout expired?)")
```

---

## Integration Examples

### Example 1: Basic Escrow Flow

```python
from forti_escrow import FortiEscrow
import smartpy as sp

# Setup
scenario = sp.test_scenario()

escrow = FortiEscrow(
    depositor=sp.address("tz1Alice"),
    beneficiary=sp.address("tz1Bob"),
    relayer=sp.address("tz1Charlie"),
    escrow_amount=sp.nat(5_000_000),  # 5 XTZ
    timeout_seconds=sp.nat(24 * 3600)  # 24 hours
)
scenario += escrow

# Step 1: Depositor funds escrow
scenario += escrow.fund_escrow().run(
    amount=sp.utils.nat_to_tez(5_000_000),
    sender=sp.address("tz1Alice")
)

# Step 2: Service is delivered, check status
status = scenario.compute(escrow.get_status())
assert status.state == "FUNDED"
assert status.timeout_expired == False

# Step 3: Depositor releases funds to beneficiary
scenario += escrow.release_funds().run(
    sender=sp.address("tz1Alice")
)

# Verify completion
final_status = scenario.compute(escrow.get_status())
assert final_status.state == "RELEASED"
```

---

### Example 2: Recovery After Timeout

```python
from forti_escrow import FortiEscrow
import smartpy as sp

scenario = sp.test_scenario()

escrow = FortiEscrow(
    depositor=sp.address("tz1Alice"),
    beneficiary=sp.address("tz1Bob"),
    relayer=sp.address("tz1Charlie"),
    escrow_amount=sp.nat(1_000_000),
    timeout_seconds=sp.nat(100)  # 100 seconds for testing
)
scenario += escrow

# Fund escrow
scenario += escrow.fund_escrow().run(
    amount=sp.utils.nat_to_tez(1_000_000),
    sender=sp.address("tz1Alice")
)
assert escrow.data.state == "FUNDED"

# Wait for timeout to expire
scenario += sp.test_scenario().h.past(scenario, sp.nat(150))

# Anyone can trigger recovery
scenario += escrow.force_refund().run(
    sender=sp.address("tz1David"),  # Attacker/observer, doesn't matter
    now=sp.timestamp_type().make(150)
)

# Verify funds returned to depositor
assert escrow.data.state == "REFUNDED"
assert sp.balance(escrow.address) == sp.tez(0)
```

---

### Example 3: Off-Chain Coordination

```python
# Client-side code for monitoring

import requests
import json
from datetime import datetime

ESCROW_ADDRESS = "KT1..."

def check_escrow_status():
    """Query escrow status from blockchain indexer"""
    
    # Call RPC to get contract storage
    response = requests.post(
        "https://ghostnet.ecadinfra.com/chains/main/blocks/head/context/contracts/KT1.../storage",
        json={}
    )
    
    storage = response.json()
    
    status = {
        "state": storage["state"],
        "amount": int(storage["amount"]),
        "timeout_expires": datetime.fromtimestamp(
            int(storage["funded_timestamp"]) + int(storage["timeout_seconds"])
        ),
        "can_release": storage["state"] == "FUNDED",
        "can_force_refund": datetime.now() > datetime.fromtimestamp(
            int(storage["funded_timestamp"]) + int(storage["timeout_seconds"])
        )
    }
    
    return status

def print_escrow_summary():
    status = check_escrow_status()
    
    print(f"Escrow State: {status['state']}")
    print(f"Amount: {status['amount']} mutez")
    
    if status['state'] == 'FUNDED':
        print(f"Timeout expires: {status['timeout_expires']}")
        if status['can_release']:
            print("✓ Depositor can call release_funds()")
        if status['can_force_refund']:
            print("✓ Anyone can call force_refund() (recovery available)")
```

---

## Security Best Practices

### Deployment Checklist

Before deploying to mainnet:

1. **Verify Addresses**
   ```python
   assert depositor != beneficiary, "Depositor and beneficiary must be different"
   assert depositor != "", "Depositor must be set"
   assert beneficiary != "", "Beneficiary must be set"
   ```

2. **Verify Amount**
   ```python
   assert escrow_amount > 0, "Amount must be positive"
   assert escrow_amount < 1_000_000_000, "Amount seems unreasonably large"
   ```

3. **Verify Timeout**
   ```python
   assert timeout_seconds >= 3600, "Timeout must be at least 1 hour"
   assert timeout_seconds <= 365 * 24 * 3600, "Timeout seems unreasonably long"
   ```

4. **Test on Ghostnet**
   ```bash
   # Deploy to testnet first
   tezos-client -N https://ghostnet.ecadinfra.com ...
   
   # Verify all transitions work
   # Test timeout recovery
   # Verify fund amounts
   ```

5. **Audit Trail**
   - Save deployment transaction hash
   - Document all parties and amounts
   - Record deployment timestamp

### Operational Best Practices

1. **Monitor Timeout Windows**
   - Set reminders for timeout expiration
   - Track multiple escrows in a spreadsheet
   - Alert on unusual activity

2. **Key Management**
   - Use hardware wallets for depositor keys
   - Keep relayer credentials secure
   - Rotate keys periodically

3. **Dispute Resolution**
   - Document all off-chain agreements
   - Keep communication records
   - Use timeout as enforcer, not resolver

---

## Troubleshooting

### Issue: "INVALID_STATE" Error

**Cause**: Attempting transition from wrong state

**Solution**:
```python
status = escrow.get_status()
print(f"Current state: {status['state']}")

# Verify you're in the right state for your operation
# INIT: can only fund
# FUNDED: can release or refund
# RELEASED/REFUNDED: terminal, no operations
```

---

### Issue: "UNAUTHORIZED" Error

**Cause**: Caller is not authorized for operation

**Solution**:
```python
# release_funds() → only depositor
# refund_escrow() → only depositor (before timeout)
# force_refund() → anyone (but only after timeout)

status = escrow.get_status()
if status['state'] == 'FUNDED':
    if status['timeout_expired']:
        # Anyone can force_refund()
        escrow.force_refund().run(sender=any_address)
    else:
        # Only depositor can release/refund
        escrow.release_funds().run(sender=depositor)
```

---

### Issue: "INSUFFICIENT_FUNDS" or "TIMEOUT_NOT_REACHED"

**Cause**: Amount doesn't match or timeout hasn't passed

**Solution**:
```python
# Check exact amount required
status = escrow.get_status()
required_amount = sp.utils.nat_to_tez(status['amount'])

# Fund with exact amount
escrow.fund_escrow().run(amount=required_amount)

# For force_refund, check timeout
print(f"Time until refund available: {status['timeout_expires'] - now}")
```

---

## Advanced: Multi-Escrow Management

For applications managing multiple escrows:

```python
class EscrowManager:
    """Manages multiple FortiEscrow instances"""
    
    def __init__(self):
        self.escrows = {}  # {escrow_id: contract_address}
    
    def create_escrow(self, depositor, beneficiary, relayer, amount, timeout):
        """Deploy new escrow contract"""
        contract = FortiEscrow(
            depositor=depositor,
            beneficiary=beneficiary,
            relayer=relayer,
            escrow_amount=amount,
            timeout_seconds=timeout
        )
        # Deploy contract, get address
        escrow_id = f"{depositor}_{beneficiary}_{time.time()}"
        self.escrows[escrow_id] = contract.address
        return escrow_id
    
    def check_all_statuses(self):
        """Check status of all escrows"""
        for escrow_id, address in self.escrows.items():
            contract = FortiEscrow.at(address)
            status = contract.get_status()
            if status.timeout_expired and status.state == "FUNDED":
                print(f"⚠️  {escrow_id} available for recovery!")
    
    def force_recover_expired(self):
        """Recover all expired escrows"""
        for escrow_id, address in self.escrows.items():
            contract = FortiEscrow.at(address)
            if contract.can_transition("REFUNDED"):
                contract.force_refund().run(sender=manager_address)
                print(f"✓ Recovered {escrow_id}")
```

---

## FAQ

**Q: Can the relayer steal funds?**  
A: No. The relayer has no special privileges. Only the depositor can release funds.

**Q: What if the beneficiary refuses to receive funds?**  
A: If the address is invalid, release will fail and revert. Depositor can then refund.

**Q: Can I modify the timeout after creation?**  
A: No. Timeout is immutable. This is intentional (security guarantee).

**Q: What if I deploy with wrong addresses?**  
A: You must deploy a new contract. There's no way to change parties.

**Q: Who pays for gas (transaction fees)?**  
A: The caller pays. Depositor funds escrow, either party can call state transitions.

**Q: Can I use this for NFTs or tokens?**  
A: Current version handles XTZ only. For tokens, see FortiEscrow-Token variant.

---

**Version**: 1.0.0  
**Last Updated**: January 25, 2026
