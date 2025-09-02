#!/bin/bash

# CI/CD Status Checker for AdCP Demo
# This script checks the current status of the CI/CD pipeline

set -e

echo "🔍 Checking CI/CD Pipeline Status for AdCP Demo..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a file exists
file_exists() {
    [ -f "$1" ]
}

# Function to check if a directory exists
dir_exists() {
    [ -d "$1" ]
}

# Function to print status
print_status() {
    local status="$1"
    local message="$2"
    
    case $status in
        "OK")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠️  $message${NC}"
            ;;
        "ERROR")
            echo -e "${RED}❌ $message${NC}"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ️  $message${NC}"
            ;;
    esac
}

echo "📋 Configuration Files:"
if file_exists "pyproject.toml"; then
    print_status "OK" "pyproject.toml - Pytest configuration"
else
    print_status "ERROR" "pyproject.toml - Missing pytest configuration"
fi

if file_exists "requirements-dev.txt"; then
    print_status "OK" "requirements-dev.txt - Development dependencies"
else
    print_status "ERROR" "requirements-dev.txt - Missing development dependencies"
fi

if file_exists ".flake8"; then
    print_status "OK" ".flake8 - Flake8 linting configuration"
else
    print_status "ERROR" ".flake8 - Missing flake8 configuration"
fi

if file_exists "mypy.ini"; then
    print_status "OK" "mypy.ini - MyPy type checking configuration"
else
    print_status "ERROR" "mypy.ini - Missing mypy configuration"
fi

if file_exists ".pre-commit-config.yaml"; then
    print_status "OK" ".pre-commit-config.yaml - Pre-commit hooks"
else
    print_status "ERROR" ".pre-commit-config.yaml - Missing pre-commit configuration"
fi

echo ""
echo "🚀 CI/CD Workflows:"
if dir_exists ".github/workflows"; then
    if file_exists ".github/workflows/ci.yml"; then
        print_status "OK" "Main CI/CD pipeline workflow"
    else
        print_status "ERROR" "Main CI/CD pipeline workflow missing"
    fi
    
    if file_exists ".github/workflows/pr-checks.yml"; then
        print_status "OK" "PR checks workflow"
    else
        print_status "ERROR" "PR checks workflow missing"
    fi
    
    if file_exists ".github/workflows/deploy-staging.yml"; then
        print_status "OK" "Staging deployment workflow"
    else
        print_status "ERROR" "Staging deployment workflow missing"
    fi
else
    print_status "ERROR" ".github/workflows directory missing"
fi

echo ""
echo "🔧 Development Tools:"
if command_exists "python3"; then
    print_status "OK" "Python 3 installed"
else
    print_status "ERROR" "Python 3 not found"
fi

if dir_exists "venv"; then
    print_status "OK" "Virtual environment exists"
else
    print_status "WARNING" "Virtual environment not found (run: ./scripts/setup-ci.sh)"
fi

if file_exists "Makefile"; then
    print_status "OK" "Enhanced Makefile with CI targets"
else
    print_status "ERROR" "Makefile not found"
fi

echo ""
echo "🧪 Testing Infrastructure:"
if dir_exists "tests"; then
    TEST_COUNT=$(find tests -name "test_*.py" | wc -l)
    print_status "OK" "Test directory with $TEST_COUNT test files"
else
    print_status "ERROR" "Tests directory missing"
fi

if file_exists "pytest.ini"; then
    print_status "OK" "Pytest configuration (fallback)"
else
    print_status "INFO" "Using pyproject.toml for pytest configuration"
fi

echo ""
echo "📊 Current Status Summary:"

# Count issues
ERROR_COUNT=0
WARNING_COUNT=0
OK_COUNT=0

# Check critical components
if ! file_exists "pyproject.toml"; then ERROR_COUNT=$((ERROR_COUNT + 1)); fi
if ! file_exists "requirements-dev.txt"; then ERROR_COUNT=$((ERROR_COUNT + 1)); fi
if ! dir_exists ".github/workflows"; then ERROR_COUNT=$((ERROR_COUNT + 1)); fi
if ! file_exists "Makefile"; then ERROR_COUNT=$((ERROR_COUNT + 1)); fi
if ! dir_exists "tests"; then ERROR_COUNT=$((ERROR_COUNT + 1)); fi

if ! dir_exists "venv"; then WARNING_COUNT=$((WARNING_COUNT + 1)); fi

echo ""
if [ $ERROR_COUNT -eq 0 ]; then
    print_status "OK" "All critical components are in place!"
    echo ""
    echo "🚀 Ready to run CI/CD pipeline:"
    echo "  ./scripts/setup-ci.sh    - Set up development environment"
    echo "  ./scripts/run-ci-local.sh - Run full CI pipeline locally"
    echo "  make ci-full             - Run CI pipeline via Makefile"
    echo "  make help                - Show all available commands"
else
    print_status "ERROR" "Found $ERROR_COUNT critical issues that need to be resolved"
    echo ""
    echo "🔧 Issues to fix:"
    if ! file_exists "pyproject.toml"; then echo "  - Create pyproject.toml"; fi
    if ! file_exists "requirements-dev.txt"; then echo "  - Create requirements-dev.txt"; fi
    if ! dir_exists ".github/workflows"; then echo "  - Create .github/workflows directory"; fi
    if ! file_exists "Makefile"; then echo "  - Create Makefile"; fi
    if ! dir_exists "tests"; then echo "  - Create tests directory"; fi
fi

if [ $WARNING_COUNT -gt 0 ]; then
    echo ""
    print_status "WARNING" "Found $WARNING_COUNT warnings"
    echo "  - These won't prevent CI/CD from working but should be addressed"
fi

echo ""
echo "📚 Documentation:"
echo "  - README.md - Project overview and setup"
echo "  - docs/ - Detailed documentation"
echo "  - .github/workflows/ - CI/CD workflow definitions"
echo "  - scripts/ - Automation scripts"

