# Contributing to AdCP Demo

Thank you for your interest in contributing to AdCP Demo! This document outlines the development standards, processes, and quality gates that ensure code quality and project health.

## 🚀 **CI/CD Pipeline - Quality First Development**

This project uses a **comprehensive automated CI/CD pipeline** that **MUST** pass before any code can be merged. The pipeline addresses specific issues in the codebase and provides automated quality gates for continuous development.

### **Quality Gates (Enforced)**
- ✅ **70% minimum code coverage** (CI fails if below threshold)
- ✅ **All tests must pass** (unit, integration, RAG, MCP)
- ✅ **Security scans must pass** (Bandit + Safety)
- ✅ **Code formatting compliance** (Black + isort)
- ✅ **Linting compliance** (Flake8)
- ✅ **Type checking compliance** (MyPy)

## 📋 **Prerequisites**

### **Required Tools**
- Python 3.9+
- Git
- Make (for development commands)

### **Development Environment Setup**
```bash
# Clone the repository
git clone <repository-url>
cd ocrs5

# Setup CI/CD environment
./scripts/setup-ci.sh

# Verify setup
./scripts/ci-status.sh
```

## 🔧 **Development Workflow**

### **1. Branch Strategy**
- **Main branch**: `main` - Production-ready code
- **Development branch**: `develop` - Integration branch
- **Feature branches**: `feature/description` - New features
- **Bug fix branches**: `fix/description` - Bug fixes

### **2. Feature Development Process**
```bash
# 1. Create feature branch from develop
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name

# 2. Make changes following quality standards
# (See Quality Standards section below)

# 3. Run local CI pipeline
./scripts/run-ci-local.sh

# 4. Commit changes with proper messages
git add .
git commit -m "feat: add new feature description"

# 5. Push and create pull request
git push origin feature/your-feature-name
```

### **3. Pull Request Process**
1. **Create PR** from feature branch to `develop`
2. **CI/CD pipeline runs automatically** (required)
3. **All quality gates must pass** (no exceptions)
4. **Code review** by maintainers
5. **Merge only after approval** and all checks pass

## 📏 **Code Quality Standards**

### **Code Coverage**
- **Minimum**: 70% (enforced by CI)
- **Target**: 80% (recommended)
- **New features**: Must include tests
- **Bug fixes**: Must include regression tests

### **Code Formatting**
```bash
# Format code before committing
make fmt

# Check formatting compliance
make fmt-check
```

**Standards:**
- **Line length**: 100 characters maximum
- **Formatter**: Black (enforced)
- **Import sorting**: isort (enforced)
- **Indentation**: 4 spaces (no tabs)

### **Linting and Type Checking**
```bash
# Run all quality checks
make lint
make type-check
make security
```

**Standards:**
- **Linting**: Flake8 compliance (enforced)
- **Type hints**: Required for all functions (enforced)
- **Security**: No high-severity issues (enforced)
- **Complexity**: Maximum cyclomatic complexity of 10

### **Testing Standards**
```bash
# Run specific test types
make test-unit        # Unit tests (fast)
make test-integration # Integration tests (medium)
make test-rag         # RAG functionality tests
make test-mcp         # MCP protocol tests
make test-coverage    # All tests with coverage
```

**Standards:**
- **Unit tests**: Required for all functions
- **Integration tests**: Required for workflows
- **RAG tests**: Required for search functionality
- **MCP tests**: Required for protocol implementation
- **Test markers**: Use appropriate pytest markers

### **Test Markers**
```python
import pytest

@pytest.mark.unit
def test_unit_function():
    """Test individual function behavior."""
    pass

@pytest.mark.integration
def test_integration_workflow():
    """Test complete workflow integration."""
    pass

@pytest.mark.rag
def test_rag_functionality():
    """Test RAG search and filtering."""
    pass

@pytest.mark.mcp
def test_mcp_protocol():
    """Test MCP protocol implementation."""
    pass

@pytest.mark.web_grounding
def test_web_context():
    """Test web context grounding."""
    pass

@pytest.mark.slow
def test_slow_operation():
    """Test operations that take time."""
    pass
```

## 🚫 **Prohibited Practices**

### **Code Quality Violations**
- ❌ **Debug logging in production code** (use proper logging levels)
- ❌ **Unhandled exceptions** (always handle or document)
- ❌ **Hardcoded secrets** (use environment variables)
- ❌ **Unused imports or variables** (clean up code)
- ❌ **Functions longer than 50 lines** (break down complexity)
- ❌ **Classes longer than 200 lines** (consider refactoring)

### **Security Violations**
- ❌ **SQL injection vulnerabilities** (use parameterized queries)
- ❌ **Command injection** (validate all inputs)
- ❌ **Information disclosure** (log only necessary data)
- ❌ **Weak authentication** (use secure methods)

### **Testing Violations**
- ❌ **Tests that don't run** (fix or remove)
- ❌ **Tests without assertions** (meaningful assertions required)
- ❌ **Tests that depend on external services** (mock external calls)
- ❌ **Tests that are too slow** (mark as slow, optimize)

## 🔍 **Pre-commit Checks**

### **Automatic Hooks**
Pre-commit hooks run automatically on every commit:
```bash
# Install hooks (done during setup)
pre-commit install

# Run manually
make pre-commit
```

**Hooks include:**
- Code formatting (Black + isort)
- Linting (Flake8)
- Type checking (MyPy)
- Security scanning (Bandit)
- Dependency security (Safety)
- Basic file checks

### **Manual Quality Checks**
```bash
# Run before committing
make fmt-check      # Check formatting
make lint           # Run linting
make type-check     # Check types
make security       # Security scan
make test-fast      # Run fast tests
```

## 📊 **CI/CD Pipeline Details**

### **Pipeline Stages**
1. **Code Quality & Security** (15 min)
   - Security analysis, formatting, linting, types
2. **Unit Tests** (20 min)
   - Matrix: Python 3.9, 3.10, 3.11
3. **Integration Tests** (30 min)
   - Full workflow testing
4. **RAG & MCP Tests** (25 min)
   - Critical path testing
5. **Performance Tests** (20 min)
   - Benchmarks and load testing
6. **Coverage & Quality Gates** (15 min)
   - 70% threshold enforcement
7. **Smoke Tests** (10 min)
   - Application verification
8. **Final Quality Gate** (10 min)
   - Overall status check

### **Quality Gate Enforcement**
- **Coverage below 70%**: CI fails, merge blocked
- **Tests failing**: CI fails, merge blocked
- **Security issues**: CI fails, merge blocked
- **Formatting issues**: CI fails, merge blocked
- **Type errors**: CI fails, merge blocked

## 🐛 **Bug Fixes**

### **Bug Report Requirements**
- **Clear description** of the issue
- **Steps to reproduce** (if applicable)
- **Expected vs actual behavior**
- **Environment details** (OS, Python version, etc.)
- **Error logs** (if applicable)

### **Bug Fix Process**
```bash
# 1. Create fix branch
git checkout -b fix/bug-description

# 2. Fix the issue
# 3. Add regression test
# 4. Run local CI pipeline
./scripts/run-ci-local.sh

# 5. Commit and push
git commit -m "fix: resolve bug description"
git push origin fix/bug-description
```

## ✨ **New Features**

### **Feature Request Requirements**
- **Clear description** of the feature
- **Use case** and benefits
- **Technical approach** (if applicable)
- **Impact** on existing functionality

### **Feature Development Process**
```bash
# 1. Create feature branch
git checkout -b feature/feature-name

# 2. Implement feature
# 3. Add comprehensive tests
# 4. Update documentation
# 5. Run local CI pipeline
./scripts/run-ci-local.sh

# 6. Commit and push
git commit -m "feat: add feature description"
git push origin feature/feature-name
```

## 📚 **Documentation**

### **Required Documentation**
- **Code comments**: Complex logic explanation
- **Function docstrings**: Google style format
- **README updates**: New features and changes
- **API documentation**: Endpoint changes
- **Configuration**: New environment variables

### **Documentation Standards**
```python
def complex_function(param1: str, param2: int) -> bool:
    """
    Brief description of what the function does.
    
    Args:
        param1: Description of first parameter
        param2: Description of second parameter
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When parameters are invalid
        
    Example:
        >>> result = complex_function("test", 42)
        >>> print(result)
        True
    """
    # Implementation here
    pass
```

## 🔄 **Code Review Process**

### **Review Requirements**
- **All CI checks must pass** (no exceptions)
- **Code coverage maintained** (70% minimum)
- **Security scans clean** (no vulnerabilities)
- **Documentation updated** (if applicable)
- **Tests added** (for new functionality)

### **Review Checklist**
- [ ] Code follows style guidelines
- [ ] Tests pass and coverage maintained
- [ ] Security scans clean
- [ ] Documentation updated
- [ ] No debug code in production
- [ ] Error handling appropriate
- [ ] Performance considerations addressed

## 🚨 **Emergency Fixes**

### **Hotfix Process**
For critical production issues:
1. **Create hotfix branch** from `main`
2. **Minimal changes** to fix the issue
3. **Run essential tests** only
4. **Deploy to production** after review
5. **Merge back to develop** with full CI pipeline

## 📞 **Getting Help**

### **CI/CD Issues**
1. Check pipeline status: `./scripts/ci-status.sh`
2. Review [CI/CD Setup Guide](docs/CI_CD_SETUP.md)
3. Run local pipeline: `./scripts/run-ci-local.sh`
4. Check GitHub Actions logs

### **Development Issues**
1. Review this contributing guide
2. Check [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
3. Run quality checks: `make help`
4. Ask in project discussions

## 🎯 **Success Metrics**

### **Individual Contributors**
- **Code coverage**: Maintain or improve
- **CI pipeline**: Always pass before merging
- **Security**: Zero high-severity issues
- **Documentation**: Keep updated

### **Project Health**
- **Overall coverage**: Target 80%
- **Build success rate**: Target 95%+
- **Security issues**: Zero in production
- **Code quality**: Consistent standards

## 📝 **Commit Message Standards**

### **Format**
```
type(scope): description

[optional body]

[optional footer]
```

### **Types**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test additions or changes
- `chore`: Maintenance tasks

### **Examples**
```
feat(rag): add hybrid search strategy selection
fix(mcp): resolve session timeout issues
docs(api): update endpoint documentation
style: format code with black and isort
refactor(orchestrator): break down large functions
test(web_grounding): add comprehensive test coverage
chore: update dependencies
```

## 🎉 **Recognition**

### **Quality Contributions**
- **Consistent CI pipeline success**
- **High test coverage**
- **Clean security scans**
- **Well-documented code**
- **Helpful code reviews**

### **Community Impact**
- **Helping other contributors**
- **Improving documentation**
- **Suggesting process improvements**
- **Reporting and fixing issues**

---

**Remember**: The CI/CD pipeline is your friend! It catches issues early and ensures code quality. Always run it locally before pushing, and never merge code that doesn't pass all quality gates.

Thank you for contributing to AdCP Demo! 🚀

