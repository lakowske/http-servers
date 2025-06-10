# Verification Tests

## Purpose

These tests **verify** that your running system is working correctly without making any changes. They are completely **safe to run** against your operational system.

## What These Tests Do

- ✅ **READ-ONLY**: Never modify system state
- ✅ **Safe**: Can run against live operational system
- ✅ **Fast**: Complete in under 2 seconds
- ✅ **Reliable**: Use graceful fallbacks for missing components

## Test Categories

### `TestBasicSystemHealth`
- Verifies workspace structure is intact
- Checks config files exist and are readable
- Validates configuration loads successfully
- Confirms build directory is accessible

### `TestContainerStatus`
- Queries container status (doesn't start/stop)
- Checks HTTP container if it exists
- Checks mail container if it exists
- Gracefully handles missing containers

### `TestCommandLineInterface`
- Verifies build.py is executable
- Tests CLI commands work (read-only)
- Validates Python environment has required packages

## Running

### VS Code Test Explorer
- Shows only verification tests by default
- Click any test to run it
- Safe to run anytime

### Command Line
```bash
# Run all verification tests
pytest -m verification

# Run specific test class
pytest tests/verification/test_system_health.py::TestBasicSystemHealth

# Run with verbose output
pytest -m verification -v
```

## Integration with Task Explorer

**Recommended Workflow:**
1. 🚀 **Task Explorer**: Make system changes (start containers, etc.)
2. ✅ **Verification Tests**: Click to verify everything works
3. 🔄 **Repeat**: Make more changes, verify again

This gives you confidence that your system changes worked correctly!

## Next Steps

As we build out the test suite, we'll add:
- `tests/integration/` - Isolated tests with cleanup
- `tests/config/` - Configuration file testing
- More verification tests for specific features

But these basic health checks give you a solid foundation for verifying your system!
