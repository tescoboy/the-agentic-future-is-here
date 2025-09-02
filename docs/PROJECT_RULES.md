# Project Rules

This document defines the **mandatory project rules** for AdCP Demo. These rules are **enforced by the CI/CD pipeline** and must be followed by all contributors and maintainers.

## 🚨 **Mandatory Rules (Enforced by CI/CD)**

### **Rule 1: CI/CD Pipeline Must Pass**
- **Enforcement**: GitHub Actions workflows
- **Requirement**: All quality gates must pass
- **Consequence**: Merge blocked if pipeline fails
- **Scope**: Every commit, push, and pull request

### **Rule 2: Code Coverage Threshold**
- **Enforcement**: Pytest coverage check
- **Requirement**: Minimum 70% code coverage
- **Target**: 80% code coverage
- **Consequence**: CI fails if below threshold

### **Rule 3: Code Quality Standards**
- **Enforcement**: Automated tools + CI pipeline
- **Requirements**: Black, isort, Flake8, MyPy compliance
- **Consequence**: CI fails if standards not met
- **Scope**: All Python code

### **Rule 4: Security Requirements**
- **Enforcement**: Bandit + Safety scans
- **Requirement**: Zero high-severity vulnerabilities
- **Consequence**: CI fails if security issues found
- **Scope**: All code and dependencies

## 📋 **Development Rules**

### **Rule 5: Pre-commit Checks**
- **Enforcement**: Git hooks + CI pipeline
- **Requirement**: All pre-commit checks must pass
- **Consequence**: Commit blocked locally, CI fails remotely
- **Tools**: Black, isort, Flake8, MyPy, Bandit, Safety

### **Rule 6: Testing Requirements**
- **Enforcement**: Pytest + coverage reporting
- **Requirements**: 
  - Unit tests for all functions
  - Integration tests for workflows
  - RAG tests for search functionality
  - MCP tests for protocol implementation
- **Consequence**: CI fails if tests fail or coverage drops

### **Rule 7: Documentation Standards**
- **Enforcement**: Code review + CI checks
- **Requirements**: 
  - Function docstrings (Google style)
  - README updates for new features
  - API documentation updates
  - Configuration documentation
- **Consequence**: Code review blocked if documentation incomplete

### **Rule 8: Code Structure Limits**
- **Enforcement**: Linting + code review
- **Limits**:
  - Functions: Maximum 50 lines
  - Classes: Maximum 200 lines
  - Files: Maximum 500 lines
  - Line length: Maximum 100 characters
- **Consequence**: Linting fails, code review blocked

## 🔒 **Security Rules**

### **Rule 9: Input Validation**
- **Enforcement**: Code review + security scans
- **Requirement**: All inputs must be validated
- **Scope**: User inputs, API parameters, file uploads
- **Consequence**: Security scan fails, merge blocked

### **Rule 10: Authentication & Authorization**
- **Enforcement**: Code review + security scans
- **Requirement**: Secure authentication methods only
- **Scope**: All user-facing operations
- **Consequence**: Security scan fails, merge blocked

### **Rule 11: Data Protection**
- **Enforcement**: Code review + security scans
- **Requirements**:
  - No sensitive data in logs
  - Use environment variables for secrets
  - Encrypt sensitive data
  - Implement access controls
- **Consequence**: Security scan fails, merge blocked

## 🧪 **Testing Rules**

### **Rule 12: Test Coverage**
- **Enforcement**: Pytest + coverage reporting
- **Requirements**:
  - New features: 90% coverage (target), 80% (minimum)
  - Bug fixes: Maintain or improve coverage
  - Critical paths: 95% coverage (target), 90% (minimum)
- **Consequence**: CI fails if coverage requirements not met

### **Rule 13: Test Quality**
- **Enforcement**: Pytest + code review
- **Requirements**:
  - All tests must run successfully
  - Tests must have meaningful assertions
  - External dependencies must be mocked
  - Slow tests must be marked appropriately
- **Consequence**: CI fails if test quality requirements not met

### **Rule 14: Test Organization**
- **Enforcement**: Code review + CI checks
- **Requirements**:
  - Use appropriate pytest markers
  - Organize tests by type (unit, integration, e2e)
  - Maintain test fixtures and utilities
  - Keep tests fast and reliable
- **Consequence**: Code review blocked if organization poor

## 📝 **Documentation Rules**

### **Rule 15: Code Documentation**
- **Enforcement**: Code review + linting
- **Requirements**:
  - Google style docstrings for all functions
  - Class and module docstrings
  - Complex logic comments
  - API endpoint documentation
- **Consequence**: Code review blocked if documentation incomplete

### **Rule 16: Project Documentation**
- **Enforcement**: Code review + CI checks
- **Requirements**:
  - README updates for new features
  - API documentation updates
  - Configuration documentation
  - Troubleshooting guides
- **Consequence**: Code review blocked if documentation incomplete

## 🔄 **Workflow Rules**

### **Rule 17: Branch Strategy**
- **Enforcement**: Git workflow + CI pipeline
- **Requirements**:
  - Feature branches from `develop`
  - Bug fix branches from `develop`
  - Hotfix branches from `main`
  - Proper branch naming conventions
- **Consequence**: CI pipeline may fail, code review blocked

### **Rule 18: Pull Request Process**
- **Enforcement**: GitHub + CI pipeline
- **Requirements**:
  - CI/CD pipeline must pass
  - Code review approval required
  - All feedback must be addressed
  - Documentation must be updated
- **Consequence**: Merge blocked until all requirements met

### **Rule 19: Commit Standards**
- **Enforcement**: Pre-commit hooks + CI pipeline
- **Requirements**:
  - Conventional commit messages
  - Meaningful commit descriptions
  - No debug code in commits
  - Proper scope and type
- **Consequence**: Commit blocked locally, CI fails remotely

## 🚫 **Prohibited Practices**

### **Rule 20: Code Quality Violations**
- **Prohibited**:
  - Debug logging in production code
  - Unhandled exceptions
  - Hardcoded secrets
  - Unused imports or variables
  - Functions longer than 50 lines
  - Classes longer than 200 lines
  - Files longer than 500 lines
- **Consequence**: CI fails, merge blocked

### **Rule 21: Security Violations**
- **Prohibited**:
  - SQL injection vulnerabilities
  - Command injection
  - Information disclosure
  - Weak authentication
  - Hardcoded credentials
- **Consequence**: CI fails, merge blocked

### **Rule 22: Testing Violations**
- **Prohibited**:
  - Tests that don't run
  - Tests without assertions
  - Tests depending on external services
  - Tests that are too slow (unmarked)
- **Consequence**: CI fails, merge blocked

## 📊 **Enforcement Mechanisms**

### **Automated Enforcement**
- **Pre-commit hooks**: Run on every commit
- **CI/CD pipeline**: Run on every push/PR
- **Quality gates**: Block merges if standards not met
- **Coverage enforcement**: Fail if below 70%

### **Manual Enforcement**
- **Code review**: Maintainer approval required
- **Documentation review**: Standards compliance check
- **Performance review**: Algorithm efficiency check
- **Security review**: Vulnerability assessment

## 🔧 **Tools and Configuration**

### **Required Tools**
- **Black**: Code formatting (enforced)
- **isort**: Import sorting (enforced)
- **Flake8**: Linting (enforced)
- **MyPy**: Type checking (enforced)
- **Pytest**: Testing (enforced)
- **Bandit**: Security scanning (enforced)
- **Safety**: Dependency security (enforced)

### **Configuration Files**
- `pyproject.toml`: Pytest and project configuration
- `.flake8`: Linting configuration
- `mypy.ini`: Type checking configuration
- `.pre-commit-config.yaml`: Pre-commit hooks
- `.github/workflows/`: CI/CD pipeline definitions

## 📚 **Documentation References**

### **Required Reading**
- [CI/CD Setup Guide](CI_CD_SETUP.md) - Complete setup and usage
- [Development Standards](DEVELOPMENT_STANDARDS.md) - Code quality standards
- [Contributing Guide](../CONTRIBUTING.md) - Contribution process
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Common issues and solutions

### **Quick Reference**
- [Implementation Summary](../CI_CD_IMPLEMENTATION_SUMMARY.md) - What was built
- [README](../README.md) - Project overview and quick start
- [Makefile](../Makefile) - Available commands and targets

## 🎯 **Success Metrics**

### **Individual Contributors**
- **CI pipeline**: 100% success rate
- **Code coverage**: Maintain or improve
- **Security**: Zero high-severity issues
- **Documentation**: Keep updated

### **Project Health**
- **Overall coverage**: Target 80%
- **Build success rate**: Target 95%+
- **Security issues**: Zero in production
- **Code quality**: Consistent standards

## 🚨 **Violation Consequences**

### **First Violation**
- **Warning**: Code review feedback
- **Requirement**: Fix and resubmit
- **Timeline**: Within 24 hours

### **Repeated Violations**
- **Block**: Merge requests blocked
- **Requirement**: Maintainer review required
- **Timeline**: Until standards met

### **Critical Violations**
- **Immediate**: Merge blocked
- **Requirement**: Security review required
- **Timeline**: Until security issues resolved

## 📞 **Getting Help**

### **Rule Violations**
1. **Check CI/CD logs** for specific errors
2. **Review documentation** for standards
3. **Run local checks** before pushing
4. **Ask maintainers** for clarification

### **Standards Questions**
1. **Review this document** for specific rules
2. **Check development standards** for details
3. **Review contributing guide** for process
4. **Ask in project discussions**

## 🔄 **Rule Updates**

### **Process**
1. **Proposal**: Submit rule change proposal
2. **Discussion**: Team review and discussion
3. **Approval**: Maintainer approval required
4. **Implementation**: Update documentation and CI
5. **Communication**: Notify all contributors

### **Timeline**
- **Minor changes**: 1 week notice
- **Major changes**: 2 weeks notice
- **Critical changes**: Immediate implementation

---

## 📋 **Rule Compliance Checklist**

Before submitting any code, ensure compliance with all rules:

- [ ] **CI/CD pipeline passes** all quality gates
- [ ] **Code coverage maintained** at 70% minimum
- [ ] **All tests pass** (unit, integration, RAG, MCP)
- [ ] **Security scans clean** (no vulnerabilities)
- [ ] **Code formatting compliant** (Black + isort)
- [ ] **Linting passes** (Flake8 compliance)
- [ ] **Type checking passes** (MyPy compliance)
- [ ] **Documentation updated** (docstrings, README)
- [ ] **Pre-commit checks pass** (all hooks)
- **Code review approved** by maintainer

**Remember**: These rules are **enforced by the CI/CD pipeline**. Code that doesn't comply will not be merged. Always run quality checks locally before pushing, and use the provided tools to maintain compliance.

The goal is **high-quality, maintainable code** that can be safely refactored and extended. 🚀

