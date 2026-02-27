# Contributing to FortiEscrow

Thank you for your interest in contributing to FortiEscrow! This document provides guidelines and instructions for contributing.

## Getting Started

### Prerequisites

- Python 3.9+
- Git
- pip (Python package manager)

### Local Development Setup

```bash
# Clone the repository
git clone https://github.com/FortiEscrow/FortiEscrow.git
cd FortiEscrow

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install pytest pytest-cov black flake8 isort
```

### Running Tests Locally

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run specific test suite
python3 -m pytest tests/unit/test_dispute_mechanism.py -v

# Run with coverage
python3 -m pytest tests/ --cov=contracts --cov-report=html

# Run security tests
python3 -m pytest tests/adversarial/ -v
```

## Development Workflow

### 1. Create a Feature Branch

Follow this naming convention:
- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `hotfix/description` - Critical production fixes
- `docs/description` - Documentation updates
- `test/description` - Testing improvements
- `refactor/description` - Code refactoring

```bash
git checkout -b feature/my-feature-name
```

### 2. Make Changes

#### Code Style

We follow PEP 8 with these tools:

```bash
# Format code with Black
black contracts/ tests/

# Check import sorting with isort
isort contracts/ tests/

# Lint with Flake8
flake8 contracts/ tests/
```

#### Commit Messages

Use **semantic commit messages** for clarity:

```
type(scope): subject

body

footer
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Tests
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `chore`: Build, dependencies, CI/CD
- `style`: Code style (formatting)
- `ci`: CI/CD configuration

**Examples:**
```
feat(dispute): allow voting during active disputes

- Remove DISPUTE_ACTIVE_VOTING_BLOCKED guard
- Enable arbiter participation in voting
- Add comprehensive tests

Closes #42
```

```
fix(escrow): prevent double-release

Fixes #37
```

### 3. Submit a Pull Request

1. Push your branch to GitHub:
   ```bash
   git push origin feature/my-feature-name
   ```

2. Open a Pull Request on GitHub

3. Fill out the PR template completely:
   - ✅ Semantic commit format
   - ✅ Tests passing (38/40 minimum)
   - ✅ Code coverage maintained (75%+)
   - ✅ Security scan passing
   - ✅ Documentation updated

4. Address review feedback

## Testing Requirements

### Test Coverage

- **Target:** 75% code coverage minimum
- **Dispute Mechanism:** 21/21 tests PASSING
- **Overall Suite:** 38/40 tests PASSING

```bash
# Generate coverage report
pytest tests/ --cov=contracts --cov-report=html --cov-report=term-missing
```

### Running Dispute Mechanism Tests

The core of FortiEscrow is thoroughly tested:

```bash
pytest tests/unit/test_dispute_mechanism.py -v

# Expected output: 21 passed
```

### Security Testing

```bash
# Run adversarial tests
pytest tests/adversarial/ -v

# Run invariant verification
pytest tests/invariant/ -v
```

## Code Review Process

### Automated Checks (CI/CD)

When you submit a PR, these checks automatically run:

1. **Tests** (`tests.yml`)
   - Python 3.9, 3.10, 3.11
   - All test suites
   - Coverage reporting

2. **Security** (integrated in `codeql.yml`)
   - CodeQL analysis
   - Bandit security scan
   - Dependency vulnerability check

3. **Code Quality** (`tests.yml`)
   - Black formatting
   - isort import sorting
   - Flake8 linting

4. **Documentation** (maintained in `/docs` directory)
   - Markdown validation
   - Link checking
   - API doc generation

All checks must pass before merging.

### Manual Review

At least one maintainer must review and approve the PR:

- **Code Review:** Logic, security, style
- **Testing:** Adequate test coverage
- **Documentation:** Updated docs/comments
- **Backward Compatibility:** No breaking changes (unless documented)

## Security Considerations

### When Contributing Security Fixes

1. **DO NOT** open a public issue for the vulnerability
2. **DO** email `security@fortiescrow.dev` with details
3. **DO** provide a PR with the fix under a private branch
4. **DO** include test cases that verify the fix

### Security Guidelines

- ✅ Validate all inputs
- ✅ Follow the CEI (Checks-Effects-Interactions) pattern
- ✅ Use explicit state checks
- ✅ Maintain invariant properties
- ✅ Add security comments for non-obvious code

## Documentation

### Updating Documentation

1. **API Changes:** Update `docs/API.md`
2. **Security:** Update `docs/SECURITY.md`
3. **Deployment:** Update `docs/DEPLOYMENT.md`
4. **Semantics:** Update `docs/SEMANTICS.md` for behavior changes

### Code Comments

- Explain **why**, not what
- Security-critical code gets extra comments
- Use `[SECURITY]`, `[INVARIANT]`, `[GUARD]` tags for important sections

Example:
```python
# [GUARD] Prevent voting after consensus (CRITICAL)
# SECURITY: Allows only one resolution per escrow
sp.verify(
    not self.data.consensus_executed,
    "CONSENSUS_ALREADY_EXECUTED"
)
```

## Common Tasks

### Running a Single Test

```bash
pytest tests/unit/test_dispute_mechanism.py::test_resolve_dispute_release -xvs
```

### Debugging Tests

```bash
# Run with detailed output
pytest tests/unit/test_dispute_mechanism.py -xvs

# Run with pdb breakpoints
pytest tests/unit/test_dispute_mechanism.py --pdb
```

### Checking What Changed

```bash
# See unstaged changes
git diff

# See staged changes
git diff --cached

# See changes in current branch vs main
git diff main..
```

## Getting Help

- **Questions?** Open a GitHub Discussion
- **Bug Reports?** Open an issue with the bug template
- **Security Concerns?** Email security@fortiescrow.dev
- **Feature Ideas?** Open an issue with the feature template

## License

By contributing to FortiEscrow, you agree that your contributions will be licensed under the same license as the project (see LICENSE).

---

**Thank you for contributing to FortiEscrow! Your help makes the escrow protocol more secure and robust for everyone.** 🙏
