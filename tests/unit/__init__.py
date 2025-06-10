"""
Unit tests - fast, isolated tests with no external dependencies.

These tests are suitable for:
- Pre-commit hooks (run automatically before each commit)
- GitHub Actions CI (run without containers)
- Development feedback loops (run quickly during coding)

Characteristics:
- No external dependencies (files, network, containers)
- Run in milliseconds, not seconds
- Pure functions and business logic testing
- Mocked external dependencies
"""
