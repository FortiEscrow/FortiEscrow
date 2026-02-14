# FortiEscrow Tests

Comprehensive test suite organized by verification category.

## Structure

```
tests/
├── unit/                           # Functional correctness
│   ├── test_simple_escrow.py       # SimpleEscrow entrypoints
│   ├── test_multisig_escrow.py     # MultiSigEscrow entrypoints
│   ├── test_basic_escrow.py        # Core functionality (fund, release, refund)
│   ├── test_reusability.py         # Framework reusability validation
│   └── test_framework_structure.py # Module imports and structure smoke tests
│
├── adversarial/                    # Attack simulation and security
│   ├── test_adversarial_smartpy.py # SmartPy adversarial scenarios
│   ├── test_attack_scenarios.py    # Authorization, state, timing attacks
│   ├── test_security_fixes.py      # Regression tests for security patches
│   └── test_fund_lock_prevention.py # Fund-locking attack prevention
│
└── invariant/                      # Formal property verification
    ├── test_invariants.py          # 5 security invariants validation
    ├── test_semantic_properties.py # FSM semantics without SmartPy runtime
    ├── test_audit_verification.py  # Audit-grade formal property checks
    └── test_contract_verification.py # AST-based contract structure validation
```

## Running Tests

```bash
# All tests
python -m pytest tests/ -v

# By category
python -m pytest tests/unit/ -v
python -m pytest tests/adversarial/ -v
python -m pytest tests/invariant/ -v

# With coverage
python -m pytest tests/ --cov=contracts/
```
