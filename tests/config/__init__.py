"""
Configuration tests - validate config parsing and validation logic.

These tests are suitable for:
- Pre-commit hooks (fast validation)
- GitHub Actions CI (no container dependencies)
- Configuration changes validation

Characteristics:
- Test configuration parsing logic
- Validate configuration schemas
- Test configuration merging/updating
- Use temporary files, not real config.yaml
"""
