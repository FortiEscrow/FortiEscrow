## 📋 Pull Request Checklist

- [ ] PR title follows semantic commit format (`type: description`)
- [ ] All tests passing (38/40 target minimum)
- [ ] Dispute mechanism tests validated
- [ ] Code coverage maintained (75%+ required)
- [ ] Security scan passed
- [ ] Documentation updated (if applicable)
- [ ] No breaking changes (or clearly documented)
- [ ] Commits are squashed/clean

## 📝 Description

<!--
Provide a clear and concise description of the changes this PR makes.
What problem does it solve? What feature does it add?
-->

## 🔗 Related Issues

<!--
Link related issues here with `#issue_number` or `Closes #issue_number`
Example: `Fixes #123`
-->

## 🧪 Testing

<!--
Describe the tests you've added or modified:
- Unit tests: (list)
- Integration tests: (list)
- Security tests: (list)
-->

## 📊 Test Results

```
Run the following and paste output:
python3 -m pytest tests/ -v --tb=short
```

**Test Summary:**
- Total Tests: 
- Passed: 
- Failed: 
- Coverage: 

## 🔒 Security Impact

- [ ] No security impact
- [ ] Security improvement
- [ ] Security bug fix

If applicable, describe the security implications:

## 📚 Documentation

<!--
What documentation has been updated?
- [ ] README.md
- [ ] docs/API.md
- [ ] docs/SECURITY.md
- [ ] Inline code comments
- [ ] Other: 
-->

## 🔄 Breaking Changes

- [ ] No breaking changes
- [ ] Breaking changes (document below)

If breaking changes:

## 📸 Screenshots / Demos

<!--
If applicable, add screenshots or demo videos
-->

## 👥 Reviewers

<!--
Tag anyone who should review this PR
-->

## ℹ️ Additional Context

<!--
Add any other context about the PR that would be helpful for reviewers
-->

---

### Automated Checks
- 🔄 Tests: (will be checked by CI/CD)
- 🔒 Security: (will be checked by CodeQL)
- 📊 Coverage: (will be checked by Codecov)
- 📝 Lint: (will be checked by Flake8/Black)

**Note:** Make sure all automated checks pass before merging. Read [CONTRIBUTING.md](https://github.com/FortiEscrow/FortiEscrow/blob/main/CONTRIBUTING.md) for guidelines.
