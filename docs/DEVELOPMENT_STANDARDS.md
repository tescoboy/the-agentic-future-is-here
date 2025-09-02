# Development Standards

This document defines the **mandatory development standards** for AdCP Demo. These standards are **enforced by the CI/CD pipeline** and must be followed for all code contributions.

## 🚨 **Mandatory Standards (Enforced by CI/CD)**

### **Code Coverage**
- **Minimum**: 70% (CI fails if below)
- **Target**: 80% (recommended)
- **Enforcement**: Coverage check in CI pipeline
- **Scope**: All new and modified code

### **Code Quality**
- **Formatting**: Black + isort compliance (enforced)
- **Linting**: Flake8 compliance (enforced)
- **Types**: MyPy type checking (enforced)
- **Security**: Bandit + Safety scans (enforced)

### **Testing Requirements**
- **Unit tests**: Required for all functions
- **Integration tests**: Required for workflows
- **RAG tests**: Required for search functionality
- **MCP tests**: Required for protocol implementation
- **Coverage**: Must maintain or improve overall coverage

## 📏 **Code Structure Standards**

### **Function Length**
- **Maximum**: 50 lines per function
- **Target**: 30 lines or less
- **Reasoning**: Improves readability and testability
- **Enforcement**: Linting and code review

### **Class Length**
- **Maximum**: 200 lines per class
- **Target**: 100 lines or less
- **Reasoning**: Prevents monolithic classes
- **Enforcement**: Linting and code review

### **File Length**
- **Maximum**: 500 lines per file
- **Target**: 300 lines or less
- **Reasoning**: Improves maintainability
- **Enforcement**: Linting and code review

### **Line Length**
- **Maximum**: 100 characters
- **Target**: 80 characters
- **Reasoning**: Improves readability
- **Enforcement**: Black formatter

## 🔒 **Security Standards**

### **Input Validation**
- **All inputs must be validated** before processing
- **Use parameterized queries** for database operations
- **Sanitize user input** to prevent injection attacks
- **Validate file uploads** and content types

### **Authentication & Authorization**
- **Use secure authentication methods** (OAuth, JWT, etc.)
- **Implement proper session management**
- **Validate user permissions** for all operations
- **Log authentication events** for security monitoring

### **Data Protection**
- **Never log sensitive data** (passwords, tokens, PII)
- **Use environment variables** for secrets
- **Encrypt sensitive data** at rest and in transit
- **Implement proper access controls**

### **Error Handling**
- **Don't expose internal errors** to users
- **Log errors appropriately** for debugging
- **Use custom exception classes** for business logic
- **Handle exceptions gracefully** with fallbacks

## 🧪 **Testing Standards**

### **Test Coverage Requirements**
```python
# Example: Function with comprehensive testing
def calculate_rag_score(query: str, product: dict) -> float:
    """
    Calculate RAG relevance score for a product.
    
    Args:
        query: User search query
        product: Product information
        
    Returns:
        Relevance score between 0.0 and 1.0
        
    Raises:
        ValueError: If query is empty or product is invalid
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")
    
    if not product or not isinstance(product, dict):
        raise ValueError("Product must be a valid dictionary")
    
    # Implementation here
    return 0.85

# Required test coverage
def test_calculate_rag_score_valid_inputs():
    """Test RAG score calculation with valid inputs."""
    result = calculate_rag_score("luxury car", {"name": "BMW", "description": "Luxury vehicle"})
    assert 0.0 <= result <= 1.0
    assert isinstance(result, float)

def test_calculate_rag_score_empty_query():
    """Test RAG score calculation with empty query."""
    with pytest.raises(ValueError, match="Query cannot be empty"):
        calculate_rag_score("", {"name": "BMW"})

def test_calculate_rag_score_invalid_product():
    """Test RAG score calculation with invalid product."""
    with pytest.raises(ValueError, match="Product must be a valid dictionary"):
        calculate_rag_score("luxury car", None)
```

### **Test Organization**
```
tests/
├── unit/                    # Unit tests (fast)
│   ├── test_rag.py        # RAG functionality tests
│   ├── test_mcp.py        # MCP protocol tests
│   └── test_utils.py      # Utility function tests
├── integration/            # Integration tests (medium)
│   ├── test_workflows.py  # End-to-end workflow tests
│   └── test_apis.py       # API integration tests
├── e2e/                   # End-to-end tests (slow)
│   └── test_buyer_flow.py # Complete buyer journey tests
└── fixtures/              # Test fixtures and utilities
    ├── conftest.py        # Pytest configuration
    └── test_data.py       # Test data generators
```

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

## 📝 **Documentation Standards**

### **Code Documentation**
```python
def complex_algorithm(input_data: List[Dict], threshold: float = 0.7) -> Tuple[List[int], float]:
    """
    Perform complex algorithm processing on input data.
    
    This function implements a sophisticated algorithm that processes input data
    according to business rules and returns filtered results with confidence scores.
    
    Args:
        input_data: List of dictionaries containing input data. Each dictionary
                   must have 'id', 'value', and 'metadata' keys.
        threshold: Minimum confidence threshold for results. Must be between 0.0
                  and 1.0. Defaults to 0.7.
        
    Returns:
        Tuple containing:
        - List of integer IDs that meet the threshold criteria
        - Overall confidence score for the processing
        
    Raises:
        ValueError: If input_data is empty or threshold is invalid
        TypeError: If input_data contains invalid data types
        
    Example:
        >>> data = [{'id': 1, 'value': 0.8, 'metadata': 'test'}]
        >>> result_ids, confidence = complex_algorithm(data, 0.5)
        >>> print(f"Found {len(result_ids)} results with {confidence:.2f} confidence")
        Found 1 results with 0.85 confidence
        
    Note:
        This function is computationally expensive for large datasets.
        Consider using batch processing for datasets > 1000 items.
    """
    # Implementation here
    pass
```

### **Required Documentation**
- **Function docstrings**: Google style format
- **Class docstrings**: Purpose and usage
- **Module docstrings**: Overview and imports
- **Complex logic comments**: Explain business rules
- **API documentation**: Endpoint descriptions
- **Configuration**: Environment variable documentation

## 🎨 **Code Style Standards**

### **Formatting (Enforced by Black)**
```python
# Good: Clear, readable formatting
def process_user_data(
    user_id: int,
    user_data: Dict[str, Any],
    include_metadata: bool = True,
    max_items: int = 100,
) -> List[Dict[str, Any]]:
    """Process user data according to business rules."""
    # Implementation
    pass

# Bad: Poor formatting (will be auto-fixed)
def process_user_data(user_id:int,user_data:Dict[str,Any],include_metadata:bool=True,max_items:int=100)->List[Dict[str,Any]]:
    """Process user data according to business rules."""
    pass
```

### **Import Organization (Enforced by isort)**
```python
# Standard library imports
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

# Third-party imports
import httpx
import pytest
from fastapi import FastAPI, HTTPException
from sqlmodel import Session, select

# Local application imports
from app.models import User, Product
from app.services.rag import RAGProcessor
from app.utils.helpers import format_response
```

### **Naming Conventions**
```python
# Functions and variables: snake_case
def calculate_user_score(user_data: dict) -> float:
    max_score = 100.0
    current_score = 0.0
    
    for item in user_data:
        current_score += item.get('value', 0)
    
    return min(current_score, max_score)

# Classes: PascalCase
class UserDataProcessor:
    def __init__(self, config: dict):
        self.config = config
        self.processed_count = 0
    
    def process_batch(self, items: List[dict]) -> List[dict]:
        """Process a batch of items."""
        pass

# Constants: UPPER_SNAKE_CASE
MAX_RETRY_ATTEMPTS = 3
DEFAULT_TIMEOUT_SECONDS = 30
SUPPORTED_FORMATS = ['json', 'xml', 'csv']
```

## 🔍 **Code Review Standards**

### **Review Checklist**
- [ ] **Code follows style guidelines** (Black + isort)
- [ ] **Linting passes** (Flake8 compliance)
- [ ] **Type checking passes** (MyPy compliance)
- [ ] **Security scans clean** (Bandit + Safety)
- [ ] **Tests pass and coverage maintained** (70% minimum)
- [ ] **Documentation updated** (docstrings, comments)
- [ ] **No debug code in production** (proper logging levels)
- [ ] **Error handling appropriate** (exceptions, fallbacks)
- [ ] **Performance considerations addressed** (algorithms, queries)
- [ ] **Security considerations addressed** (input validation, auth)

### **Review Process**
1. **Automated checks must pass** (CI/CD pipeline)
2. **Code review by maintainers** (required)
3. **All feedback addressed** before merge
4. **Final approval** after all checks pass

## 🚫 **Prohibited Practices**

### **Code Quality Violations**
- ❌ **Debug logging in production code**
- ❌ **Unhandled exceptions**
- ❌ **Hardcoded secrets or configuration**
- ❌ **Unused imports or variables**
- ❌ **Functions longer than 50 lines**
- ❌ **Classes longer than 200 lines**
- ❌ **Files longer than 500 lines**

### **Security Violations**
- ❌ **SQL injection vulnerabilities**
- ❌ **Command injection**
- ❌ **Information disclosure in logs**
- ❌ **Weak authentication methods**
- ❌ **Hardcoded API keys or passwords**

### **Testing Violations**
- ❌ **Tests that don't run**
- ❌ **Tests without assertions**
- ❌ **Tests that depend on external services**
- ❌ **Tests that are too slow (mark as slow)**

## 📊 **Quality Metrics**

### **Coverage Targets**
- **Overall project**: 80% (target), 70% (minimum)
- **New features**: 90% (target), 80% (minimum)
- **Critical paths**: 95% (target), 90% (minimum)
- **Utility functions**: 100% (target), 95% (minimum)

### **Performance Targets**
- **API response time**: < 500ms (95th percentile)
- **Database queries**: < 100ms (95th percentile)
- **Test execution**: < 5 minutes (full suite)
- **CI pipeline**: < 30 minutes (total)

### **Security Targets**
- **Vulnerability scans**: 0 high-severity issues
- **Dependency security**: 0 known vulnerabilities
- **Code quality**: 0 critical linting errors
- **Type safety**: 0 critical type errors

## 🔧 **Enforcement Mechanisms**

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

## 📚 **Resources and References**

### **Tools and Configuration**
- **Black**: Code formatting (`.black` config)
- **isort**: Import sorting (`.isort` config)
- **Flake8**: Linting (`.flake8` config)
- **MyPy**: Type checking (`mypy.ini` config)
- **Pytest**: Testing (`pyproject.toml` config)

### **Documentation**
- [CI/CD Setup Guide](CI_CD_SETUP.md)
- [Contributing Guide](../CONTRIBUTING.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [API Documentation](../README.md)

### **Best Practices**
- **Python Style Guide** (PEP 8)
- **Google Python Style Guide**
- **FastAPI Best Practices**
- **SQLModel Best Practices**

---

**Remember**: These standards are **enforced by the CI/CD pipeline**. Code that doesn't meet these standards will not be merged. Always run quality checks locally before pushing, and use the provided tools to maintain consistency.

The goal is **high-quality, maintainable code** that can be safely refactored and extended. 🚀

