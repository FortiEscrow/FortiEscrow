# Deployment Guide

## Prerequisites

- Python 3.8+
- SmartPy CLI installed
- Tezos wallet with XTZ for deployment fees

```bash
pip install smartpy
```

## Compilation

### Compile Contract

```bash
# Compile SimpleEscrow
smartpy compile contracts/core/escrow_base.py build/

# Output files
# build/SimpleEscrow/step_000_cont_0_contract.tz   (Michelson)
# build/SimpleEscrow/step_000_cont_0_storage.tz    (Initial storage)
```

### Compile with Custom Parameters

```python
import smartpy as sp
from contracts.core.escrow_base import SimpleEscrow

@sp.add_compilation_target("MyEscrow")
def compile():
    return SimpleEscrow(
        depositor=sp.address("tz1..."),
        beneficiary=sp.address("tz1..."),
        amount=sp.nat(10_000_000),      # 10 XTZ
        timeout_seconds=sp.nat(604800)  # 7 days
    )
```

## Deployment

### Using SmartPy CLI

```bash
# Deploy to Ghostnet (testnet)
smartpy originate-contract \
  --code build/SimpleEscrow/step_000_cont_0_contract.tz \
  --storage build/SimpleEscrow/step_000_cont_0_storage.tz \
  --rpc https://ghostnet.tezos.marigold.dev
```

### Using Taquito (JavaScript)

```javascript
import { TezosToolkit } from '@taquito/taquito';
import { InMemorySigner } from '@taquito/signer';

const Tezos = new TezosToolkit('https://ghostnet.tezos.marigold.dev');
Tezos.setProvider({ signer: new InMemorySigner('edsk...') });

const contract = await Tezos.contract.originate({
  code: michelsonCode,
  storage: initialStorage
});

console.log(`Contract deployed at: ${contract.contractAddress}`);
```

## Configuration Parameters

### Timeout Selection

| Use Case | Recommended Timeout |
|----------|---------------------|
| Digital goods | 24-72 hours |
| Freelance services | 7-14 days |
| Large transactions | 30 days |
| Atomic swaps | 1-4 hours |

### Amount Precision

Amounts are in mutez (1 XTZ = 1,000,000 mutez).

```python
# 1 XTZ
amount=sp.nat(1_000_000)

# 0.5 XTZ
amount=sp.nat(500_000)

# 100 XTZ
amount=sp.nat(100_000_000)
```

## Pre-Deployment Checklist

### Address Verification

- [ ] Depositor address is correct (no typos)
- [ ] Beneficiary address is correct (no typos)
- [ ] Depositor != Beneficiary
- [ ] Both addresses exist on target network

### Parameter Verification

- [ ] Amount > 0
- [ ] Timeout >= 3600 seconds (1 hour minimum)
- [ ] Timeout <= 31536000 seconds (1 year maximum)
- [ ] Timeout is appropriate for use case

### Network Selection

- [ ] Correct network selected (testnet vs mainnet)
- [ ] Sufficient XTZ for deployment fee
- [ ] RPC endpoint is responsive

## Post-Deployment Verification

### Verify Contract Storage

```bash
# Query contract storage
tezos-client get contract storage for KT1...
```

Expected output:
```
(Pair (Pair "tz1Depositor" "tz1Beneficiary")
      (Pair 0          # state = INIT
            (Pair 5000000     # escrow_amount
                  604800)))   # timeout_seconds
```

### Verify Contract Code

```bash
# Query contract code
tezos-client get contract code for KT1...
```

Compare with compiled Michelson output.

## Testing on Ghostnet

### Get Testnet XTZ

Use the Ghostnet faucet: https://faucet.ghostnet.teztnets.com/

### Deploy Test Contract

```bash
# Deploy with test parameters
smartpy originate-contract \
  --code build/SimpleEscrow/step_000_cont_0_contract.tz \
  --storage build/SimpleEscrow/step_000_cont_0_storage.tz \
  --rpc https://ghostnet.tezos.marigold.dev
```

### Execute Test Flow

```bash
# 1. Fund escrow
tezos-client transfer 5 from alice to KT1... --entrypoint fund

# 2. Check status
tezos-client run view get_status on contract KT1...

# 3. Release (or refund)
tezos-client transfer 0 from alice to KT1... --entrypoint release
```

## Mainnet Deployment

### Additional Precautions

1. **Double-check addresses**: Verify depositor and beneficiary on mainnet explorer
2. **Test on Ghostnet first**: Deploy identical contract on testnet
3. **Verify compiled code**: Compare Michelson output
4. **Start with small amount**: Test flow with minimal funds first
5. **Document deployment**: Record contract address and parameters

### Mainnet RPC Endpoints

| Provider | Endpoint |
|----------|----------|
| Tezos Foundation | https://mainnet.api.tez.ie |
| ECAD Labs | https://mainnet.ecadinfra.com |
| SmartPy | https://mainnet.smartpy.io |

## Integration

### Querying Contract State

```python
# Using PyTezos
from pytezos import pytezos

client = pytezos.using(shell='mainnet')
contract = client.contract('KT1...')

# Get status
status = contract.get_status().run_view()
print(f"State: {status['state_name']}")
print(f"Can release: {status['can_release']}")
```

### Calling Entrypoints

```python
# Fund escrow
contract.fund().with_amount(5_000_000).send()

# Release funds
contract.release().send()

# Force refund (after timeout)
contract.force_refund().send()
```

### Event Monitoring

Monitor contract operations via indexer APIs:

```python
import requests

# Query contract operations
response = requests.get(
    f"https://api.tzkt.io/v1/contracts/KT1.../operations"
)
operations = response.json()
```

## Troubleshooting

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| ESCROW_ALREADY_FUNDED | Contract already funded | Check state before funding |
| ESCROW_AMOUNT_MISMATCH | Wrong amount sent | Send exact escrow_amount |
| ESCROW_NOT_DEPOSITOR | Wrong sender | Use depositor address |
| ESCROW_TIMEOUT_NOT_EXPIRED | Deadline not passed | Wait for deadline |
| ESCROW_DEADLINE_PASSED | Release window closed | Use force_refund instead |

### Verifying Transaction Success

```bash
# Check operation status
tezos-client get receipt for <operation_hash>
```
