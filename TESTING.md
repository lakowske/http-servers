# Testing Strategy and Setup

## Overview

This project implements a comprehensive testing strategy with different test categories optimized for different use cases:

- **🚀 Task Explorer**: For operational control (start/stop system)
- **✅ Verification Tests**: For verifying live system health
- **⚡ Unit Tests**: For fast development feedback and git hooks
- **🔧 Config Tests**: For configuration validation
- **🏗️ Integration Tests**: For isolated feature testing (future)

## Test Categories

### 1. Verification Tests (`tests/verification/`)
- **Purpose**: Verify running system health without changing it
- **Safe**: READ-ONLY, never modifies system state
- **Use case**: Run after Task Explorer operations to verify success
- **Speed**: Fast (< 2 seconds)

```bash
# Run verification tests
pytest -m verification
```

### 2. Unit Tests (`tests/unit/`)
- **Purpose**: Fast, isolated testing of business logic
- **Dependencies**: None (no files, network, containers)
- **Use case**: Pre-commit hooks, development feedback
- **Speed**: Very fast (< 1 second)

```bash
# Run unit tests
pytest tests/unit/
```

### 3. Configuration Tests (`tests/config/`)
- **Purpose**: Validate configuration parsing and validation
- **Dependencies**: Temporary files only
- **Use case**: Pre-commit hooks, config changes
- **Speed**: Fast (< 1 second)

```bash
# Run config tests
pytest tests/config/
```

## Pre-commit Hooks Setup

### Installation
```bash
# Run the setup script
./scripts/setup-git-hooks.sh

# Or manually:
pip install pre-commit
pre-commit install
```

### What Runs on Each Commit
1. **Code Formatting**: Black, isort
2. **Linting**: Flake8
3. **Security**: Bandit scan
4. **Basic Checks**: Trailing whitespace, YAML validity
5. **Fast Tests**: Unit tests and config tests only
6. **Type Checking**: MyPy (optional)

### Bypassing Hooks (Not Recommended)
```bash
git commit --no-verify
```

## Test Coverage

### Measuring Coverage
```bash
# Run tests with coverage
pytest tests/unit/ tests/config/ --cov=. --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Current Coverage
- **Overall**: ~56%
- **auth/password.py**: 96% (well tested)
- **configuration/app.py**: 95% (well tested)
- **Opportunity**: Improve coverage in services/ and configuration/

### Coverage Goals
- **Unit testable code**: > 80%
- **Critical business logic**: > 90%
- **Integration code**: Measured separately

## GitHub Actions CI

### What Runs on Every Push/PR
1. **Multi-Python Testing**: Python 3.11, 3.12
2. **Code Quality**: Flake8, Black, pre-commit hooks
3. **Testing**: Unit tests + config tests with coverage
4. **Security**: Bandit scan, safety checks
5. **Coverage Upload**: Codecov integration

### No Container Dependencies
- CI runs without Docker/Podman
- Only host-based tests run in CI
- Container integration tests run locally only

## Development Workflow

### 1. **Daily Development**
```bash
# Make changes
# VS Code Test Explorer: Run verification tests
pytest -m verification

# Or run fast tests during development
pytest tests/unit/ tests/config/
```

### 2. **Before Committing**
```bash
# Pre-commit hooks run automatically
git commit -m "Your changes"

# If hooks fail, fix issues and commit again
```

### 3. **Task Explorer Integration**
1. 🚀 Use Task Explorer to change system state
2. ✅ Run verification tests to confirm success
3. 🔄 Repeat as needed

### 4. **Measuring Progress**
```bash
# Check test coverage
pytest tests/unit/ tests/config/ --cov=. --cov-report=term-missing

# View detailed HTML report
pytest tests/unit/ tests/config/ --cov=. --cov-report=html
open htmlcov/index.html
```

## VS Code Integration

### Test Discovery
- Verification tests shown by default (`-m verification`)
- Change in `.vscode/settings.json` to show different test categories

### Running Tests
- **Test Explorer**: Click to run individual tests
- **Command Palette**: "Python: Run All Tests"
- **Terminal**: Use pytest commands directly

## File Organization

```
tests/
├── verification/           # Safe verification of live system
│   ├── test_system_health.py
│   └── README.md
├── unit/                   # Fast, isolated unit tests
│   └── test_password_functions.py
├── config/                 # Configuration validation tests
│   └── test_config_validation.py
├── integration/           # Future: isolated integration tests
└── fixtures/              # Future: shared test utilities
```

## Key Benefits

### ✅ **Multiple Safety Levels**
- Verification tests: Safe for live systems
- Unit tests: No external dependencies
- Pre-commit: Catch issues before they reach repo

### ✅ **Fast Feedback**
- Unit tests: < 1 second
- Pre-commit: < 10 seconds
- CI: < 3 minutes

### ✅ **Comprehensive Coverage**
- Code quality: Flake8, Black, Bandit
- Functionality: Unit + config tests
- System health: Verification tests

### ✅ **Developer Friendly**
- VS Code integration
- Task Explorer for operations
- Clear separation of concerns

## Next Steps

1. **Expand Unit Tests**: Increase coverage of core business logic
2. **Add Integration Tests**: Isolated tests with cleanup for new features
3. **Performance Tests**: Response time verification
4. **User Management Tests**: Test the decoupled user system when implemented

## Troubleshooting

### Pre-commit Hooks Failing
```bash
# Run manually to see issues
pre-commit run --all-files

# Update hooks
pre-commit autoupdate
```

### Coverage Too Low
- Focus on testing business logic first
- Mock external dependencies in unit tests
- Integration/container code measured separately

### Tests Running Slowly
- Ensure unit tests have no I/O
- Use mocks for external dependencies
- Keep verification tests lightweight
