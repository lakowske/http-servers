# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HTTP Servers is a containerized web infrastructure management system that provides secure, self-hosted web services with minimal external dependencies. It acts as an HTTP entrypoint for Git hosting, reverse proxying, mail services, and certificate management using Apache HTTP server and Podman containers.

## Essential Commands

All commands use the `now` alias (set up via `source project.sh`):

### Environment Setup
```bash
source project.sh                    # Creates venv, installs deps, sets 'now' alias
```

### Core Build & Deploy Workflow
```bash
now build                           # Render configs and build both httpd & mail images
now create_git_repo_volume          # Create persistent Git storage
now run_httpd_container             # Start the HTTP container
now run_mail_container              # Start the mail container
now create_test_repo                # Create test Git repository
now certificates                    # Generate Let's Encrypt certificates
now reload                         # Apply certificate configuration to Apache
```

### Convenience Commands (New!)
```bash
now start                           # Complete startup: render, build, create volumes, start containers
now stop                            # Stop both HTTP and mail containers
now restart                         # Restart with fresh builds
now status                          # Comprehensive status of all services
now clean                           # Clean up all containers, images, and volumes (destructive)
```


### Container Management
```bash
now list_containers                 # List all containers and their status
now health                         # Health check for httpd container
now rm_httpd_container             # Remove httpd container
now rm_mail_container              # Remove mail container
now reload_httpd                   # Reload Apache config without restarting
```

### Build Logging
```bash
now list_build_logs                # List all build logs with timestamps and status
now view_build_log                 # View the latest build log (human-readable)
now clean_build_logs               # Clean up old logs (keeps 10 most recent per image)
```

### Volume Management
```bash
now create_mail_volume             # Create mail storage volume
now create_webdav_volume           # Create WebDAV storage volume
now remove_git_repo_volume         # Remove Git repo volume
```

### Testing
```bash
pytest                             # Run all unit tests
pytest tests/                      # Run unit tests only
pytest integration_tests/          # Run integration tests only
pytest tests/test_specific.py      # Run specific test file
```

## Architecture Overview

### Service-Oriented Design
The system uses dependency injection (`dependency-injector`) with these core services:
- **HttpdService**: Apache HTTP server & Git repository management
- **MailService**: IMAP/SMTP email server management
- **PodmanService**: Container orchestration (Podman-based)
- **CertbotService**: Let's Encrypt SSL certificate automation
- **UserService**: Authentication and user management
- **ConfigService**: Centralized configuration management

### Configuration System
- **Centralized Config Tree**: All configuration managed through unified tree structure in `configuration/`
- **Template-Driven**: Jinja2 templates generate all configuration files in `build/` directory
- **Multi-Source**: Supports CLI args and YAML files (`secrets/config.yaml`)
- **Late Binding**: Services configured only when requested

### Container Strategy
- **Podman-Based**: Uses Podman instead of Docker for container management
- **Multi-Container**: Separate containers for HTTP and mail services
- **Persistent Volumes**: Git repos, mail, and WebDAV data stored in named volumes
- **Blue-Green Deployment**: Configuration reloads without service interruption

## Development Patterns

### Configuration Management
- Primary config file: `secrets/config.yaml`
- Configuration tree renders to `build/` directory before container builds
- All services access config through dependency injection container

### Dynamic CLI System
- Commands auto-generated from decorated functions in `actions/build.py`
- Use `@cli.register()` decorator to add new commands
- All CLI commands available via `now <command>` after sourcing `project.sh`

### Template System
- Dockerfile templates in `templates/Dockerfile.httpd` and `templates/Dockerfile.mail`
- Apache config templates in `templates/` directory
- Jinja2 rendering with configuration context

### Testing Approach
- **Unit Tests**: `tests/` directory using pytest
- **Integration Tests**: `integration_tests/` directory for full service testing
- **Mock External Services**: Tests run independently without external dependencies

## Key File Locations

- `actions/build.py`: Main CLI command definitions
- `configuration/`: Configuration tree and dependency injection setup
- `services/`: All service implementations
- `auth/`: Authentication and user management
- `templates/`: Jinja2 templates for configs and Dockerfiles
- `secrets/config.yaml`: Primary configuration file (not in repo)

## Code Quality Standards

### Linting Commands
```bash
source .venv/bin/activate && python -m flake8 <file>     # Style checking
source .venv/bin/activate && python -m pylint <file>     # Code quality analysis
```

### Code Style Requirements
- **Line Length**: 120 characters max (configured in `.flake8` and `.pylintrc`)
- **Encoding**: Always specify `encoding='utf-8'` for file operations
- **Logging**: Use lazy formatting `logger.info("Message %s", var)` not f-strings
- **Imports**: Remove unused imports
- **Whitespace**: No trailing whitespace, proper blank lines between functions
- **File Endings**: Always end files with newline

### Pre-commit Standards
Before committing code, ensure:
1. `flake8` reports no errors
2. `pylint` score > 9.0/10
3. All tests pass with `pytest`

## Development Workflow

1. **Setup**: `source project.sh` to activate environment
2. **Configure**: Edit `secrets/config.yaml` with domain and email
3. **Build**: `now build` to render configs and build images
4. **Deploy**: `now create_git_repo_volume && now run_httpd_container`
5. **Certificates**: `now certificates && now reload` for HTTPS
6. **Lint**: Run linting before committing changes

## Important Notes

- The system is designed for self-hosting with minimal external dependencies
- Certificate management is automated via Let's Encrypt/Certbot
- Configuration changes can be applied without container restarts using `now reload`
- All persistent data stored in named volumes (Git repos, mail, WebDAV)
- Authentication uses Apache htpasswd format for compatibility