# CI/CD Pipeline Setup Guide

## Overview

This document describes the comprehensive CI/CD pipeline implemented for the AdCP Demo project. The pipeline addresses the specific issues identified in the codebase and provides automated quality gates for continuous development.

## Architecture

### Pipeline Components

1. **GitHub Actions Workflows**
   - `ci.yml` - Full CI/CD pipeline (runs on push/PR to main/develop)
   - `pr-checks.yml` - Fast PR checks (runs on every PR)
   - `deploy-staging.yml` - Staging deployment (runs after CI passes)

2. **Local Development Tools**
   - Enhanced Makefile with CI targets
   - Pre-commit hooks for code quality
   - Local CI pipeline runner

3. **Quality Gates**
   - Code formatting (Black + isort)
   - Linting (Flake8)
   - Type checking (MyPy)
   - Security scanning (Bandit + Safety)
   - Test coverage (70% minimum)
   - Performance benchmarks

## Quick Start

### 1. Setup Development Environment

```bash
# Run the setup script
./scripts/setup-ci.sh

# Or manually install dependencies
pip install -r requirements-dev.txt
pre-commit install
```

### 2. Check Pipeline Status

```bash
# Check what's configured and what's missing
./scripts/ci-status.sh
```

### 3. Run CI Pipeline Locally

```bash
# Run the complete pipeline locally
./scripts/run-ci-local.sh

# Or use Makefile targets
make ci-full
```

## Available Commands

### Makefile Targets

```bash
# Test targets
make test              # Run all tests with coverage
make test-unit         # Run unit tests only
make test-integration  # Run integration tests only
make test-rag          # Run RAG-related tests
make test-mcp          # Run MCP protocol tests
make test-web          # Run web grounding tests
make test-fast         # Run fast tests (exclude slow)
make test-slow         # Run slow tests only
make test-coverage     # Run tests with coverage report
make test-parallel     # Run tests in parallel

# Code quality targets
make lint              # Run code linting
make fmt               # Format code
make fmt-check         # Check code formatting
make type-check        # Run type checking
make security          # Run security checks

# CI/CD targets
make ci-setup          # Setup CI environment
make ci-test           # Run CI test suite
make ci-lint           # Run CI linting
make ci-security       # Run CI security checks
make ci-full           # Run complete CI pipeline

# Utility targets
make clean             # Clean up generated files
make smoke             # Run smoke tests
make pre-commit        # Run pre-commit checks
make benchmark         # Run performance benchmarks
make help              # Show all available commands
```

### Scripts

```bash
./scripts/setup-ci.sh      # Setup development environment
./scripts/run-ci-local.sh  # Run full CI pipeline locally
./scripts/ci-status.sh     # Check pipeline status
```

## GitHub Actions Workflows

### Main CI Pipeline (`ci.yml`)

**Triggers:** Push to main/develop, Pull Request to main/develop
**Schedule:** Daily security checks at 2 AM UTC

**Jobs:**
1. **Code Quality & Security** (15 min)
   - Security analysis (Bandit)
   - Dependency security (Safety)
   - Code formatting checks
   - Linting (Flake8)
   - Type checking (MyPy)

2. **Unit Tests** (20 min)
   - Matrix: Python 3.9, 3.10, 3.11
   - Coverage reporting
   - JUnit XML output

3. **Integration Tests** (30 min)
   - PostgreSQL service container
   - Full integration test suite
   - Coverage reporting

4. **RAG & MCP Tests** (25 min)
   - Critical path testing
   - RAG functionality tests
   - MCP protocol tests

5. **Performance Tests** (20 min)
   - Performance benchmarks
   - Load testing preparation

6. **Coverage & Quality Gates** (15 min)
   - Combine coverage reports
   - Generate HTML reports
   - Enforce 70% threshold

7. **Smoke Tests** (10 min)
   - Application startup
   - Basic functionality tests

8. **Final Quality Gate** (10 min)
   - Overall status check
   - Deployment summary

### PR Checks (`pr-checks.yml`)

**Triggers:** Pull Request to main/develop
**Purpose:** Fast feedback for developers

**Jobs:**
1. **PR Quality Checks** (15 min)
   - Code formatting
   - Linting
   - Type checking
   - Fast tests (exclude slow)
   - Coverage check

2. **Security Scan** (10 min)
   - Security analysis
   - Dependency checks

### Staging Deployment (`deploy-staging.yml`)

**Triggers:** After successful CI pipeline completion
**Purpose:** Automated staging deployment

**Jobs:**
1. **Deploy to Staging** (30 min)
   - Smoke tests against staging
   - Deployment execution
   - Verification
   - Team notification

## Configuration Files

### `pyproject.toml`

- Pytest configuration with coverage settings
- Test markers for different test types
- Coverage thresholds and exclusions

### `.flake8`

- Linting rules and exclusions
- Line length: 100 characters
- Complexity limits

### `mypy.ini`

- Type checking configuration
- Strict type checking enabled
- External library exclusions

### `.pre-commit-config.yaml`

- Pre-commit hooks configuration
- Code formatting and quality checks
- Security scanning

## Test Organization

### Test Markers

```python
import pytest

@pytest.mark.unit
def test_unit_function():
    pass

@pytest.mark.integration
def test_integration_workflow():
    pass

@pytest.mark.rag
def test_rag_functionality():
    pass

@pytest.mark.mcp
def test_mcp_protocol():
    pass

@pytest.mark.web_grounding
def test_web_context():
    pass

@pytest.mark.slow
def test_slow_operation():
    pass
```

### Test Structure

```
tests/
├── unit/           # Unit tests (fast)
├── integration/    # Integration tests (medium)
├── e2e/           # End-to-end tests (slow)
├── performance/    # Performance benchmarks
└── fixtures/      # Test fixtures and utilities
```

## Quality Gates

### Coverage Threshold

- **Minimum:** 70% code coverage
- **Target:** 80% code coverage
- **Enforcement:** CI pipeline fails if below threshold

### Security Requirements

- **Bandit:** No high-severity security issues
- **Safety:** No known vulnerable dependencies
- **Enforcement:** Security scans must pass

### Code Quality

- **Formatting:** Black + isort compliance
- **Linting:** Flake8 compliance
- **Types:** MyPy type checking
- **Enforcement:** All checks must pass

## Troubleshooting

### Common Issues

1. **Coverage Below Threshold**
   ```bash
   # Generate coverage report
   make test-coverage
   
   # View HTML report
   open htmlcov/index.html
   ```

2. **Type Checking Errors**
   ```bash
   # Run type checking
   make type-check
   
   # Fix common issues
   make fmt
   ```

3. **Security Issues**
   ```bash
   # Run security checks
   make security
   
   # View reports
   cat bandit-report.json
   cat safety-report.json
   ```

### Local Development

```bash
# Setup environment
./scripts/setup-ci.sh

# Check status
./scripts/ci-status.sh

# Run pipeline locally
./scripts/run-ci-local.sh

# Quick checks
make pre-commit
```

## Performance Optimization

### Test Parallelization

```bash
# Run tests in parallel
make test-parallel

# Configure parallel workers
pytest -n auto --dist=loadfile
```

### Coverage Optimization

- Exclude generated files
- Focus on critical paths
- Use coverage markers strategically

### CI Pipeline Optimization

- Parallel job execution
- Caching dependencies
- Selective test execution

## Next Steps

1. **Immediate Actions**
   - Run `./scripts/setup-ci.sh` to setup environment
   - Run `./scripts/ci-status.sh` to check configuration
   - Test local pipeline with `./scripts/run-ci-local.sh`

2. **Integration**
   - Push to GitHub to trigger workflows
   - Monitor CI pipeline execution
   - Address any failing quality gates

3. **Customization**
   - Adjust coverage thresholds
   - Add project-specific quality rules
   - Configure deployment targets

4. **Team Adoption**
   - Share pipeline documentation
   - Train team on quality gates
   - Establish review processes

## Support

For issues with the CI/CD pipeline:

1. Check the pipeline status: `./scripts/ci-status.sh`
2. Review GitHub Actions logs
3. Run local pipeline: `./scripts/run-ci-local.sh`
4. Check configuration files
5. Review this documentation

The pipeline is designed to catch issues early and provide clear feedback for resolution.

