#!/bin/bash

# Local CI Pipeline Runner for AdCP Demo
# This script runs the complete CI pipeline locally

set -e  # Exit on any error

echo "🚀 Running complete CI pipeline locally..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "Makefile" ]; then
    print_error "Makefile not found. Please run this script from the project root."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_warning "Virtual environment not found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements-dev.txt
else
    source venv/bin/activate
fi

# Function to run a step and handle errors
run_step() {
    local step_name="$1"
    local command="$2"
    
    print_status "Running: $step_name"
    if eval "$command"; then
        print_success "$step_name completed successfully"
    else
        print_error "$step_name failed"
        return 1
    fi
}

# Start CI pipeline
echo ""
print_status "Starting CI pipeline..."

# Step 1: Code Quality & Security
echo ""
print_status "Step 1/8: Code Quality & Security"
run_step "Security checks" "make security"
run_step "Code formatting check" "make fmt-check"
run_step "Linting" "make lint"
run_step "Type checking" "make type-check"

# Step 2: Unit Tests
echo ""
print_status "Step 2/8: Unit Tests"
run_step "Unit tests" "make test-unit"

# Step 3: Integration Tests
echo ""
print_status "Step 3/8: Integration Tests"
run_step "Integration tests" "make test-integration"

# Step 4: RAG & MCP Tests
echo ""
print_status "Step 4/8: RAG & MCP Tests"
run_step "RAG tests" "make test-rag"
run_step "MCP tests" "make test-mcp"

# Step 5: Performance Tests
echo ""
print_status "Step 5/8: Performance Tests"
run_step "Performance benchmarks" "make benchmark"

# Step 6: Coverage & Quality Gates
echo ""
print_status "Step 6/8: Coverage & Quality Gates"
run_step "Test coverage" "make test-coverage"

# Step 7: Smoke Tests
echo ""
print_status "Step 7/8: Smoke Tests"
run_step "Smoke tests" "make smoke"

# Step 8: Final Quality Gate
echo ""
print_status "Step 8/8: Final Quality Gate"

# Check coverage threshold
COVERAGE_OUTPUT=$(make test-coverage 2>&1)
if echo "$COVERAGE_OUTPUT" | grep -q "FAIL Required test coverage of 70% not reached"; then
    print_error "Coverage threshold not met (70%)"
    exit 1
fi

print_success "Coverage threshold met (70%)"

# Final summary
echo ""
echo "🎉 CI Pipeline completed successfully!"
echo ""
echo "📊 Summary:"
echo "  ✅ Code quality checks passed"
echo "  ✅ Security scans completed"
echo "  ✅ All tests passed"
echo "  ✅ Coverage threshold met"
echo "  ✅ Smoke tests passed"
echo ""
echo "🚀 Code is ready for deployment!"
echo ""
echo "📁 Generated reports:"
echo "  - Coverage report: htmlcov/index.html"
echo "  - Security reports: bandit-report.json, safety-report.json"
echo "  - Test results: Various XML files"
echo ""
echo "🔧 Next steps:"
echo "  1. Review coverage report"
echo "  2. Check security reports for any issues"
echo "  3. Deploy to staging environment"
echo "  4. Run integration tests against staging"
