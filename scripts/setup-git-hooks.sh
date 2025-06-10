#!/bin/bash
# Setup git hooks for code quality and testing

set -e

echo "Setting up git hooks for HTTP Servers project..."

# Ensure we're in the project root
if [ ! -f "requirements.txt" ] || [ ! -d ".git" ]; then
    echo "Error: This script must be run from the project root directory"
    exit 1
fi

# Install pre-commit if not already installed
echo "Installing pre-commit..."
python -m pip install pre-commit

# Install the git hook scripts
echo "Installing pre-commit hooks..."
pre-commit install

# Install commit-msg hook for conventional commits (optional)
pre-commit install --hook-type commit-msg

# Run pre-commit on all files to check setup
echo "Testing pre-commit setup..."
pre-commit run --all-files || echo "Some hooks failed - this is normal on first run"

echo ""
echo "✅ Git hooks setup complete!"
echo ""
echo "What happens now:"
echo "- Before each commit: Code formatting, linting, unit tests, and config tests run automatically"
echo "- Fast tests only (no containers) - suitable for git hooks"
echo "- If any check fails, the commit is blocked"
echo ""
echo "To bypass hooks temporarily (not recommended):"
echo "  git commit --no-verify"
echo ""
echo "To run hooks manually:"
echo "  pre-commit run --all-files"
echo ""
echo "Test coverage can be measured with:"
echo "  pytest tests/unit/ tests/config/ --cov=. --cov-report=html"
echo "  # Then open htmlcov/index.html in a browser"