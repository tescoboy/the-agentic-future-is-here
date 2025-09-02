#!/bin/bash

# CI/CD Setup Script for AdCP Demo
# This script sets up the development environment for CI/CD

set -e  # Exit on any error

echo "🚀 Setting up CI/CD environment for AdCP Demo..."

# Check if we're in a CI environment
if [ "$CI" = "true" ]; then
    echo "🔧 Running in CI environment"
    export PIP_CACHE_DIR="$HOME/.cache/pip"
    export PYTHONPATH="${PYTHONPATH}:${PWD}"
else
    echo "💻 Running in local environment"
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install development dependencies
echo "📚 Installing development dependencies..."
pip install -r requirements-dev.txt

# Install pre-commit hooks
echo "🔗 Installing pre-commit hooks..."
pre-commit install

# Verify installation
echo "✅ Verifying installation..."
python -c "import pytest, black, isort, flake8, mypy, bandit, safety; print('All tools installed successfully')"

# Run initial checks
echo "🔍 Running initial code quality checks..."
make fmt-check
make lint

echo "🎉 CI/CD environment setup completed successfully!"
echo ""
echo "Available commands:"
echo "  make help           - Show all available commands"
echo "  make test           - Run all tests with coverage"
echo "  make ci-full        - Run complete CI pipeline locally"
echo "  make pre-commit     - Run pre-commit checks"
echo "  make fmt            - Format code"
echo "  make lint           - Lint code"
echo "  make security       - Run security checks"
echo ""
echo "Git hooks are now active - they will run automatically on commit/push"

