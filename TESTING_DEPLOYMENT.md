# FortiEscrow Testing & Deployment Guide

## Prerequisites

### SmartPy Installation

SmartPy is the smart contract language for Tezos. Installation varies by OS.

#### macOS / Linux
```bash
# Install from source (recommended)
git clone https://github.com/smartpy-io/smartpy.git
cd smartpy
python3 -m pip install -e .

# Or use Docker (alternative)
docker pull smartpy/smartpy
```

#### Windows
```powershell
# Use WSL2 + Linux instructions above
# Or Docker with:
docker pull smartpy/smartpy
```

### Alternative: Docker Setup
```bash
# Pull SmartPy Docker image
docker pull smartpy/smartpy

# Run tests in container
docker run -v $(pwd):/workspace smartpy/smartpy \
  python -m smartpy test /workspace/tests/test_fortiescrow.py
```

---

## Running Tests

### Local Setup
```bash
# 1. Install SmartPy (see above)
# 2. Install dependencies
pip3 install -r requirements.txt

# 3. Run full test suite
python3 -m smartpy test tests/

# 4. Run specific test
python3 -m smartpy test tests/test_fortiescrow.py

# 5. Generate report
make coverage
```

### Test Files

- **tests/test_fortiescrow.py** - Core escrow tests (1,200+ lines)
  - Happy path flows
  - Authorization checks
  - State machine validation
  - Timeout mechanisms
  - Attack prevention

- **tests/test_multisig_escrow.py** - Multi-signature variant tests
- **tests/test_simple_escrow.py** - Simplified escrow tests

### Expected Output
```
Testing FortiEscrow...
✓ test_happy_path_release
✓ test_happy_path_refund
✓ test_unauthorized_release
✓ test_invalid_state_transition
✓ test_timeout_recovery
...

Results: 23 passed, 0 failed
Coverage: 100%
```

---

## Deployment

### Testnet (Ghostnet)

```bash
# 1. Compile contract
python3 -m smartpy compile contracts/core/forti_escrow.py ./build

# 2. Check compiled .tz file
ls -la build/

# 3. Deploy to testnet
./scripts/deployment/deploy_testnet.sh
```

### Mainnet

⚠️ **Production Deployment Checklist**:
- [ ] All tests passing (23/23)
- [ ] Security audit completed
- [ ] Addresses verified
- [ ] Timeout >= 1 hour
- [ ] Amount > 0
- [ ] depositor ≠ beneficiary

```bash
# Deploy to mainnet (requires careful review)
./scripts/deployment/deploy_mainnet.sh
```

---

## Troubleshooting

### SmartPy Not Found
```bash
# Solution 1: Install from source
git clone https://github.com/smartpy-io/smartpy.git
cd smartpy && python3 -m pip install -e .

# Solution 2: Use Docker
docker run -it smartpy/smartpy /bin/bash
```

### Test Errors
```bash
# Clear cache and retry
rm -rf __pycache__ .pytest_cache
python3 -m smartpy test tests/

# Check SmartPy version
python3 -c "import smartpy; print(smartpy.__version__)"
```

### Gas Estimation
```bash
# Estimate gas costs
python3 -m smartpy estimate contracts/core/forti_escrow.py

# Results shown for each entrypoint
```

---

## Build Output

After compilation:

```
build/
├── forti_escrow.tz          # Michelson bytecode (deploy this)
├── forti_escrow.json        # Contract ABI
├── forti_escrow_storage.tz  # Storage template
└── forti_escrow_code.tz     # Code only
```

Upload `.tz` file to Better Call Dev for verification.

---

## Development Workflow

```bash
# 1. Make changes to contract
vim contracts/core/forti_escrow.py

# 2. Run tests immediately
python3 -m smartpy test tests/test_fortiescrow.py

# 3. Check compilation
python3 -m smartpy compile contracts/core/forti_escrow.py ./build

# 4. Verify gas costs
python3 -m smartpy estimate contracts/core/forti_escrow.py

# 5. Commit and push
git add -A && git commit -m "Update escrow logic"
git push
```

---

## Resources

- **SmartPy Docs**: https://smartpy.io
- **Tezos Docs**: https://tezos.com
- **Better Call Dev**: https://better-call.dev
- **Contract Audit**: See [SECURITY.md](../SECURITY.md)

---

**Last Updated**: January 25, 2026
