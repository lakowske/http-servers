"""
Shared test fixtures for event system tests.
"""

import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Generator

import pytest

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from events import EventQueue  # noqa: E402


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp(prefix="events_test_"))
    try:
        yield temp_path
    finally:
        if temp_path.exists():
            shutil.rmtree(temp_path)


@pytest.fixture
def isolated_env(temp_dir: Path):
    """Create isolated test environment with directories and event queue."""

    class IsolatedTestEnvironment:
        """Test environment with temporary directories and event queue."""

        def __init__(self, base_dir: Path):
            self.temp_dir = base_dir
            self.queue_dir = base_dir / "events"
            self.config_dir = base_dir / "secrets"
            self.templates_dir = base_dir / "templates"

            # Create directories
            self.queue_dir.mkdir()
            self.config_dir.mkdir()
            self.templates_dir.mkdir()

            # Create event queue
            self.event_queue = EventQueue(str(self.queue_dir))

        def create_config_file(self, content: str = None) -> Path:
            """Create a test configuration file."""
            if content is None:
                content = """
admin:
  domain: test.example.com
  email: admin@test.example.com

services:
  httpd:
    enabled: true
  mail:
    enabled: true
"""
            config_file = self.config_dir / "config.yaml"
            config_file.write_text(content)
            return config_file

        def create_template_file(self, name: str, content: str = "# Test template") -> Path:
            """Create a test template file."""
            template_file = self.templates_dir / name
            template_file.write_text(content)
            return template_file

        def create_user_file(self, content: str = None) -> Path:
            """Create a test user file."""
            if content is None:
                content = json.dumps({"users": [{"username": "testuser", "password": "testpass"}]})
            user_file = self.config_dir / "unified_users.json"
            user_file.write_text(content)
            return user_file

    return IsolatedTestEnvironment(temp_dir)
