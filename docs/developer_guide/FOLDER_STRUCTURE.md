# FortiEscrow: Recommended Folder Structure

```
FortiEscrow-Labs/
│
├── 📂 contracts/                          # Core smart contract implementations
│   │
│   ├── 📂 core/                           # Base escrow logic (independent)
│   │   ├── forti_escrow.py               # Main contract (750 lines)
│   │   ├── __init__.py
│   │   └── README.md                     # Core API documentation
│   │
│   ├── 📂 variants/                       # Framework extensions (reusable)
│   │   ├── 📂 token/                      # FA1.2/FA2 token escrow variant
│   │   │   ├── forti_escrow_token.py     # Token version
│   │   │   └── README.md
│   │   ├── 📂 atomic_swap/                # Cross-chain atomic swap variant
│   │   │   ├── forti_escrow_atomic.py    # HTLC variant
│   │   │   └── README.md
│   │   ├── 📂 milestone/                  # Milestone-based releases
│   │   │   ├── forti_escrow_milestone.py # Staged release variant
│   │   │   └── README.md
│   │   └── README.md                     # Variants overview
│   │
│   ├── 📂 interfaces/                     # Contract interfaces & types
│   │   ├── types.py                      # Shared type definitions
│   │   ├── errors.py                     # Error codes (centralized)
│   │   ├── events.py                     # Event definitions
│   │   └── README.md
│   │
│   ├── 📂 utils/                          # Utility functions (adapters)
│   │   ├── storage_manager.py            # Storage helpers
│   │   ├── amount_validator.py           # Amount validation utilities
│   │   ├── timeline_manager.py           # Timeout & timeline helpers
│   │   └── README.md
│   │
│   └── README.md                         # Contracts folder overview
│
├── 📂 security/                           # Security & invariants
│   │
│   ├── 📂 invariants/                     # Formal invariants & proofs
│   │   ├── state_machine.md              # FSM invariant proofs
│   │   ├── fund_invariants.md            # Fund conservation proofs
│   │   ├── authorization_invariants.md   # Auth invariant proofs
│   │   ├── timeout_invariants.md         # Timeout mechanism proofs
│   │   └── README.md
│   │
│   ├── 📂 threat_model/                   # Threat analysis
│   │   ├── stride_analysis.md            # STRIDE analysis
│   │   ├── attack_vectors.md             # 20+ attack vectors documented
│   │   ├── mitigations.md                # Mitigation strategies
│   │   └── risk_matrix.md                # Risk assessment
│   │
│   ├── audit_checklist.md                # Pre-deployment security checklist
│   ├── SECURITY.md                       # Main security documentation
│   └── README.md
│
├── 📂 tests/                              # Comprehensive test suite
│   │
│   ├── 📂 unit/                           # Unit tests (by function)
│   │   ├── test_fund_escrow.py           # fund_escrow() tests
│   │   ├── test_release_funds.py         # release_funds() tests
│   │   ├── test_refund_escrow.py         # refund_escrow() tests
│   │   ├── test_force_refund.py          # force_refund() tests
│   │   ├── test_views.py                 # View function tests
│   │   └── README.md
│   │
│   ├── 📂 integration/                    # Integration tests (scenarios)
│   │   ├── test_happy_path.py            # Complete flow tests
│   │   ├── test_timeout_recovery.py      # Timeout mechanisms
│   │   ├── test_multi_escrow.py          # Multiple escrows
│   │   └── README.md
│   │
│   ├── 📂 security/                       # Security-focused tests
│   │   ├── test_authorization.py         # Authorization bypass attempts
│   │   ├── test_fund_locking.py          # Fund-locking prevention
│   │   ├── test_state_machine.py         # FSM violation attempts
│   │   ├── test_amount_validation.py     # Amount edge cases
│   │   └── README.md
│   │
│   ├── 📂 performance/                    # Performance & gas tests
│   │   ├── test_gas_costs.py             # Gas consumption analysis
│   │   ├── test_storage_size.py          # Storage optimization
│   │   └── README.md
│   │
│   ├── conftest.py                       # Shared test fixtures
│   ├── test_forti_escrow.py              # All tests (main entry point)
│   └── README.md
│
├── 📂 docs/                               # Comprehensive documentation
│   │
│   ├── 📂 user_guide/                     # For end users
│   │   ├── quick_start.md                # 5-minute start
│   │   ├── deployment_guide.md           # Deployment procedures
│   │   ├── operation_guide.md            # Operational procedures
│   │   └── README.md
│   │
│   ├── 📂 developer_guide/                # For developers extending it
│   │   ├── architecture.md               # Architecture overview
│   │   ├── extending_framework.md        # How to create variants
│   │   ├── code_style.md                 # Code conventions
│   │   └── README.md
│   │
│   ├── 📂 security_guide/                 # For security auditors
│   │   ├── threat_model_summary.md       # Quick threat overview
│   │   ├── audit_guide.md                # How to audit FortiEscrow
│   │   ├── security_checklist.md         # Security review checklist
│   │   └── README.md
│   │
│   ├── 📂 api_reference/                  # API documentation
│   │   ├── core_contract.md              # Core API reference
│   │   ├── error_codes.md                # All error codes
│   │   ├── type_definitions.md           # Type reference
│   │   └── README.md
│   │
│   ├── 📂 examples/                       # Usage examples
│   │   ├── basic_escrow.py               # Simple XTZ escrow
│   │   ├── token_escrow.py               # Token escrow variant
│   │   ├── atomic_swap.py                # Atomic swap example
│   │   └── README.md
│   │
│   ├── QUICK_REFERENCE.md                # 1-page cheat sheet
│   ├── README.md                         # Docs overview
│   ├── FAQ.md                            # Frequently asked questions
│   └── GLOSSARY.md                       # Terminology
│
├── 📂 scripts/                            # Utility scripts
│   │
│   ├── 📂 deployment/                     # Deployment automation
│   │   ├── compile.sh                    # Compile contracts
│   │   ├── deploy_testnet.sh             # Deploy to Ghostnet
│   │   ├── deploy_mainnet.sh             # Deploy to mainnet
│   │   └── README.md
│   │
│   ├── 📂 testing/                        # Test automation
│   │   ├── run_all_tests.sh              # Run complete test suite
│   │   ├── run_security_tests.sh         # Security tests only
│   │   ├── coverage_report.sh            # Generate coverage
│   │   └── README.md
│   │
│   ├── 📂 utils/                          # Utility scripts
│   │   ├── generate_docs.sh              # Auto-generate docs
│   │   ├── audit_checklist.sh            # Run audit checklist
│   │   └── README.md
│   │
│   └── README.md
│
├── 📂 build/                              # Build outputs (gitignore)
│   ├── compiled/                         # Compiled .tz files
│   ├── artifacts/                        # Deployment artifacts
│   └── .gitkeep
│
├── 📂 .github/                            # GitHub configuration
│   ├── workflows/
│   │   ├── test.yml                      # Run tests on push
│   │   ├── security_audit.yml            # Security checks
│   │   └── docs.yml                      # Build docs
│   └── ISSUE_TEMPLATE/
│       ├── bug_report.md
│       ├── security_issue.md
│       └── feature_request.md
│
├── 📄 README.md                           # Repository root README
├── 📄 CONTRIBUTING.md                     # Contribution guidelines
├── 📄 CODE_OF_CONDUCT.md                  # Community guidelines
├── 📄 LICENSE                             # MIT License
├── 📄 .gitignore                          # Git ignore rules
├── 📄 requirements.txt                    # Python dependencies
├── 📄 setup.py                            # Package setup
├── 📄 Makefile                            # Common tasks
├── 📄 pyproject.toml                      # Project configuration
└── 📄 CHANGELOG.md                        # Version history
```

---

## 📋 Folder Purpose Reference

### `/contracts/` - Smart Contract Code
**Purpose**: Core contract implementations organized by abstraction level

- **`core/`**: Base escrow logic (immutable, audited)
- **`variants/`**: Framework extensions (token, atomic swap, milestone-based)
- **`interfaces/`**: Shared types, errors, events (single source of truth)
- **`utils/`**: Adapter functions (storage, validation, timeline)

**Audit Benefit**: Clear separation allows auditing core logic independently from variants.

---

### `/security/` - Security & Formal Analysis
**Purpose**: Invariants, threat model, and security documentation

- **`invariants/`**: Formal proofs that security properties hold
- **`threat_model/`**: Attack surface analysis and mitigations

**Audit Benefit**: Separating invariants from code makes verification explicit and auditable.

---

### `/tests/` - Test Suite (Organized by Type)
**Purpose**: Comprehensive testing covering all code paths

- **`unit/`**: Test each entrypoint individually
- **`integration/`**: Test complete workflows
- **`security/`**: Attack and exploit attempts
- **`performance/`**: Gas and storage optimization

**Audit Benefit**: Organized tests make coverage obvious and gaps easy to spot.

---

### `/docs/` - Documentation (Organized by Audience)
**Purpose**: Comprehensive docs tailored to different users

- **`user_guide/`**: For deployers/operators
- **`developer_guide/`**: For framework extension
- **`security_guide/`**: For auditors
- **`api_reference/`**: For integration

**Audit Benefit**: Security guide documents threat model for auditors explicitly.

---

### `/scripts/` - Automation
**Purpose**: Deployment, testing, and utility automation

- **`deployment/`**: Compile and deploy workflows
- **`testing/`**: Automated test execution
- **`utils/`**: Documentation and audit helpers

---

## 🎯 Key Design Principles

### 1. **Separation of Concerns**
- Core logic isolated in `/contracts/core/`
- Variants extend without modifying core
- Utilities are reusable adapters

### 2. **Auditability**
- Security analysis separated from code
- Invariants documented alongside code
- Threat model references specific functions

### 3. **Framework Scalability**
- `/contracts/variants/` supports new contract types
- `/docs/developer_guide/` explains how to create variants
- Common interfaces prevent duplication

### 4. **Clear Governance**
- Core contract path `/contracts/core/` = immutable/audited
- Variant paths = versioned/monitored
- All changes tracked in `CHANGELOG.md`

---

## 🔍 Audit-Friendly Characteristics

✅ **Invariants Explicitly Documented**  
Each security invariant has a proof file in `/security/invariants/`

✅ **Threat Model Centralized**  
All threat analysis in `/security/threat_model/` with cross-references to code

✅ **Tests Organized by Type**  
Security tests clearly separated for focused auditing

✅ **Code-to-Docs Mapping**  
Each contract function references its test and documentation

✅ **Version Tracking**  
`CHANGELOG.md` documents all modifications

---

## 📦 Implementation Order

1. **Phase 1**: Organize core contract and tests
   - `/contracts/core/` + `/tests/unit/` + `/tests/security/`

2. **Phase 2**: Add documentation
   - `/docs/` with user_guide and developer_guide

3. **Phase 3**: Add variants
   - `/contracts/variants/` (token, atomic swap)

4. **Phase 4**: Framework maturity
   - Complete `/docs/developer_guide/`
   - Add GitHub workflows

---

## 🚀 Quick Reference: File Locations

| Need | Location |
|------|----------|
| Core contract code | `/contracts/core/forti_escrow.py` |
| Test suite | `/tests/test_forti_escrow.py` |
| Security audit | `/security/SECURITY.md` |
| Threat model | `/security/threat_model/` |
| Deployment guide | `/docs/user_guide/deployment_guide.md` |
| API reference | `/docs/api_reference/core_contract.md` |
| Examples | `/docs/examples/` |
| Quick start | `/docs/user_guide/quick_start.md` |

---

## ✨ Why This Structure?

✅ **Professional**: Follows industry standards (monorepo patterns)  
✅ **Scalable**: Easy to add variants without modifying core  
✅ **Auditable**: Security analysis separated and explicit  
✅ **Maintainable**: Clear organization reduces cognitive load  
✅ **Extensible**: Framework design supports future variants  

This structure transforms FortiEscrow from a single-use dApp into a reusable framework.
