# Contributing

## Development Setup

```bash
# Clone repository
git clone https://github.com/FortiEscrow/FortiEscrow.git
cd FortiEscrow-Labs

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v
```

## Code Style

### Python

- Follow PEP 8
- Use type hints where applicable
- Maximum line length: 100 characters

### SmartPy

- Explicit state checks before modifications
- Checks-Effects-Interactions pattern for entrypoints
- Comprehensive docstrings for public methods

### Documentation

- English only
- No emoji in documentation
- No marketing language
- Precision over brevity

## Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test File

```bash
pytest tests/test_invariants.py -v
```

### Test Coverage

```bash
pytest tests/ --cov=contracts --cov-report=html
```

## Pull Request Process

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/your-feature`
3. **Write** tests for new functionality
4. **Ensure** all tests pass
5. **Submit** pull request with clear description

### PR Requirements

- [ ] All tests pass
- [ ] New code has tests
- [ ] Documentation updated if needed
- [ ] No security invariants violated
- [ ] Code follows style guidelines

## Security Considerations

When modifying contract code:

1. **Maintain invariants**: All five security invariants must hold
2. **Add tests**: Include tests for both happy path and failure cases
3. **Document changes**: Update SECURITY.md if threat model changes
4. **Review authorization**: Verify access control is correct

### Security Invariant Checklist

- [ ] Funds Safety: transfers only in terminal states
- [ ] State Consistency: valid FSM transitions only
- [ ] Authorization: correct sender checks
- [ ] Time Safety: deadline handling correct
- [ ] No Fund-Locking: exit paths preserved

## Adding New Variants

### Create Variant

```python
# contracts/variants/my_variant/my_escrow.py
from contracts.core.escrow_base import EscrowBase

class MyEscrow(EscrowBase):
    """Docstring describing variant purpose."""

    def __init__(self, depositor, beneficiary, amount, timeout_seconds, ...):
        EscrowBase.__init__(self, depositor, beneficiary, amount, timeout_seconds)
        # Additional initialization
```

### Add Tests

```python
# tests/test_my_variant.py
def test_my_variant_happy_path():
    # Test implementation
    pass
```

### Document Variant

Update [README.md](README.md) contract variants table.

## Reporting Issues

### Bug Reports

Include:
- SmartPy version
- Python version
- Steps to reproduce
- Expected behavior
- Actual behavior

### Security Vulnerabilities

Report security issues privately to maintainers. Do not open public issues for security vulnerabilities.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
