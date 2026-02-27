# FortiEscrow GitHub Configuration

This directory contains GitHub-specific configuration and workflows for the FortiEscrow project.

## 📁 Directory Structure

### `workflows/`
Minimal but comprehensive CI/CD pipelines:

- **`tests.yml`** - Test suite across Python 3.9/3.10/3.11 with coverage
- **`codeql.yml`** - CodeQL analysis, security scanning, and dependency checking
- **`release.yml`** - Automated release creation when tags are pushed

### `ISSUE_TEMPLATE/`
GitHub issue templates for consistent issue reporting:

- **`bug_report.md`** - Report bugs with environment details
- **`feature_request.md`** - Suggest new features

### Other Files

- **`pull_request_template.md`** - PR template with checklist and guidelines
- **`CODEOWNERS`** - Define code ownership and review requirements
- **`dependabot.yml`** - Automated dependency and security updates

## 🚀 CI/CD Workflows

### Test Pipeline (`tests.yml`)

Runs on every push to main/develop and on PRs:

```
┌─────────────────────────────────────────────────┐
│ Test Suite (Python 3.9, 3.10, 3.11)             │
│ - Unit tests                                    │
│ - Dispute mechanism tests (21/21)               │
│ - All integration tests                         │
├─────────────────────────────────────────────────┤
│ Code Coverage                                   │
│ - Generate coverage report                      │
│ - Upload to Codecov                             │
│ - Comment on PR with coverage delta             │
├─────────────────────────────────────────────────┤
│ Security Scan                                   │
│ - Bandit security checks                        │
│ - Dependency vulnerability scan                 │
├─────────────────────────────────────────────────┤
│ Code Quality                                    │
│ - Black formatting check                        │
│ - isort import sorting                          │
│ - Flake8 linting                                │
├─────────────────────────────────────────────────┤
│ Dispute Tests                                   │
│ - Full dispute mechanism validation             │
│ - Multisig escrow tests                         │
└─────────────────────────────────────────────────┘
```

**Triggers:**
- Push to `main` or `develop`
- Pull requests to `main` or `develop`
- Daily schedule (0:00 UTC)

**Status Badges:**
```markdown
![Tests](https://github.com/FortiEscrow/FortiEscrow/actions/workflows/tests.yml/badge.svg)
![Security](https://github.com/FortiEscrow/FortiEscrow/actions/workflows/codeql.yml/badge.svg)
```

### Security Scanning (`codeql.yml`)

Comprehensive security analysis integrated with CodeQL workflow:

- **CodeQL Analysis** - Detect security vulnerabilities in Python code
- **Dependency Scanning** - Automated vulnerability checking with Safety
- **Bandit Security** - Python-specific security issue detection
- **SARIF Upload** - Results uploaded to GitHub Security tab

### Release Management (`release.yml`)

Automatic release creation when tags are pushed:

```bash
git tag v1.0.0
git push origin v1.0.0
```

Automatically creates:
- GitHub Release with tag
- Changelog generated from commit messages
- Release notes with dependency and testing information

## ✅ Branch Protection Rules

Recommended GitHub branch protection settings for `main`:

```yaml
Required status checks:
  - Tests (all sizes passing)
  - Security (CodeQL passed)
  - Code Quality (linting passed)
  - Coverage (75%+ maintained)

Require:
  - All conversations resolved
  - Code review (1 approval)
  - Status checks passing
  - Linear history (rebase)

Allow:
  - Auto-merge for admins
  - Dismiss stale reviews
```

## 📊 Expected Test Results

### Current Status
```
Dispute Mechanism Tests:    ✅ 21/21 PASSING
Multisig Escrow Tests:      ✅ 17/19 PASSING
Total:                       ✅ 38/40 PASSING (95%)
Code Coverage:               ✅ 80%+
Security Scan:              ✅ 0 vulnerabilities
```

### Build Status
[View latest build status →](https://github.com/FortiEscrow/FortiEscrow/actions)

## 🔧 Local Testing Before PR

Run these commands before pushing to ensure CI will pass:

```bash
# Install dev dependencies
pip install -r requirements.txt
pip install pytest pytest-cov black flake8 isort bandit

# Format code
black contracts/ tests/
isort contracts/ tests/

# Check linting
flake8 contracts/ tests/

# Run all tests
pytest tests/ -v --tb=short

# Check security
bandit -r contracts/
```

## 📝 Semantic Commit Format

All commits must follow semantic versioning:

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
- `refactor`: Refactoring
- `chore`: Build, CI/CD, dependencies
- `perf`: Performance improvement

**Examples:**
```
fix(dispute): allow voting during active disputes
feat(governance): add multi-sig voting weights
docs(api): update endpoint documentation
test(security): add adversarial test cases
chore(ci): upgrade GitHub Actions versions
```

## 🚀 Deployment

### To Production

1. Update version in `pyproject.toml`
2. Create release tag: `git tag v1.0.0`
3. Push tag: `git push origin v1.0.0`
4. Release workflow automatically:
   - Creates GitHub Release
   - Generates changelog
   - Runs final tests

### Staging/Development

Push to `develop` branch for pre-release testing.

## 📈 GitHub Statistics

View repository metrics in GitHub:

- **Insights** → See commit history, contributors
- **Actions** → View workflow run history
- **Security** → See dependency vulnerabilities
- **Code Scanning** → View code analysis results

## 🆘 Troubleshooting

### Tests Failing in CI but Passing Locally

1. Check Python version matches (3.9+)
2. Ensure `conftest.py` is in workspace root
3. Check that all `requirements.txt` packages are installed
4. Run `pytest tests/ -v --tb=long` for detailed output

### Security Scan Failing

1. Run `bandit -r contracts/` locally
2. Check for hardcoded secrets or credentials
3. Review unsafe dependencies in `requirements.txt`

### Coverage Below Threshold

```bash
pytest tests/ --cov=contracts --cov-report=term-missing
# Add tests for uncovered lines
```

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
- [SECURITY.md](../docs/SECURITY.md) - Security considerations
- [Main README.md](../README.md) - Project overview

---

**Questions?** See [CONTRIBUTING.md](../CONTRIBUTING.md) or open a GitHub Discussion.
