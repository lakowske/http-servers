# File-Based Event System

A lightweight, dependency-free configuration change notification system designed for container environments and host-based development.

## Overview

The event system enables automatic detection and processing of configuration file changes without requiring containers to restart. It uses filesystem-based communication for reliability and simplicity.

## Architecture

```
File Changes → Event Publisher → Event Queue (filesystem) → Event Subscribers → Actions
```

### Key Components

1. **Event Publisher** (`events/publisher.py`)
   - Monitors files/directories for changes using inotify or polling
   - Publishes structured events to filesystem queue
   - Supports multiple file types and recursive directory watching

2. **Event Queue** (`events/queue.py`)
   - Filesystem-based queue using directories (`pending/`, `processing/`, `completed/`, `failed/`)
   - Atomic operations for reliable event handling
   - Self-cleaning with configurable retention

3. **Event Subscriber** (`events/subscriber.py`)
   - Processes events from queue using registered handlers
   - Supports validation, rendering, reloading, and regeneration callbacks
   - Robust error handling and retry mechanisms

4. **Event Models** (`events/models.py`)
   - Pydantic models for type safety and validation
   - Event types: `CONFIG_CHANGED`, `TEMPLATE_CHANGED`, `USER_CHANGED`, `CERTIFICATE_CHANGED`
   - Change types: `CREATED`, `MODIFIED`, `DELETED`, `MOVED`

## Usage

### Host-Based Testing

```bash
# Run comprehensive demo
python demo_events.py

# Run specific demo
python demo_events.py --demo basic

# Run unit tests
python -m pytest tests/test_events.py -v

# Run integration tests (requires podman)
python -m pytest integration_tests/test_events_integration.py -v
```

### Container Integration

The system is designed for container communication via shared volumes:

```bash
# Host: Start publisher monitoring config files
events/publisher.py --queue-dir /shared/events --config-mode

# Container: Start subscriber processing events
events/subscriber.py --queue-dir /shared/events --enable-all-callbacks
```

### Event Queue Structure

```
events/
├── pending/       # New events waiting for processing
├── processing/    # Events currently being processed
├── completed/     # Successfully processed events
└── failed/        # Failed events with error details
```

## Benefits

### Development & Testing
- **Host-testable**: Works entirely on filesystem without containers
- **CI/CD friendly**: No external dependencies, runs in GitHub Actions
- **Fast feedback**: Immediate file change detection and processing
- **Isolated testing**: Each test creates clean temporary environment

### Production
- **Zero-downtime**: Configuration updates without container restarts
- **Reliable**: Filesystem-based queue survives process crashes
- **Efficient**: inotify-based monitoring with polling fallback
- **Container-ready**: Communicates via shared volumes

### Operational
- **Self-cleaning**: Automatic cleanup of old events
- **Auditable**: Complete event history and processing logs
- **Debuggable**: Clear event lifecycle and error tracking
- **Scalable**: Multiple publishers/subscribers supported

## Configuration Types Supported

1. **Main Configuration** (`secrets/config.yaml`)
   - Validates → Renders templates → Reloads containers

2. **Templates** (`templates/*.conf`)
   - Re-renders → Graceful reload → Health check

3. **User Files** (`secrets/unified_users.json`)
   - Regenerates auth files → Reloads authentication

4. **Certificates** (future)
   - Updates SSL configs → Graceful reload

## Testing Strategy

### Unit Tests (`tests/test_events.py`)
- Event queue operations (publish, claim, complete)
- File change detection (create, modify, delete)
- Event handler logic and error cases
- Subscriber processing and exception handling
- End-to-end integration scenarios

### Integration Tests (`integration_tests/test_events_integration.py`)
- Container communication via shared volumes
- Event processing within containers
- File watching reliability from containers
- Full deployment scenarios with cleanup

### Host-Based Demo (`demo_events.py`)
- Basic functionality demonstration
- Multiple file type handling
- Recursive directory watching
- Real-time processing examples

## Integration Points

### Existing System
The event system extends the current `watch_user_changes.py` pattern to handle:
- Main configuration file monitoring
- Template change detection
- Multi-service coordination
- Container reload orchestration

### Container Volumes
```yaml
volumes:
  - ./events:/shared/events           # Event queue
  - ./secrets:/shared/config          # Configuration files
  - ./templates:/shared/templates     # Template files
  - ./build:/shared/build             # Rendered configs
```

### Service Integration
```python
# Extend existing services
httpd_service.reload_configuration()  # Graceful Apache reload
mail_service.reload_postfix()         # Postfix reload
mail_service.reload_dovecot()         # Dovecot reload
```

## Next Steps

1. **Integration with existing services**: Connect to actual `ConfigService`, `HttpdService`, `MailService`
2. **Container deployment**: Add to Dockerfiles and service startup
3. **Monitoring integration**: Add metrics and health checks
4. **Performance optimization**: Tune polling intervals and batch sizes
5. **Documentation**: User guide and troubleshooting

## Key Features

- ✅ **Zero external dependencies**: Pure Python with standard library
- ✅ **Container communication**: Via shared filesystem volumes
- ✅ **Self-cleaning**: Automatic event queue maintenance
- ✅ **Comprehensive testing**: Unit, integration, and demo coverage
- ✅ **Error resilience**: Robust exception handling and retry logic
- ✅ **Type safety**: Pydantic models for all data structures
- ✅ **Multiple file types**: Config, templates, users, certificates
- ✅ **Recursive watching**: Full directory tree monitoring
- ✅ **Host development**: Works without containers for fast iteration

The event system provides a solid foundation for configuration change automation while maintaining the project's self-hosting philosophy and minimal external dependencies.
