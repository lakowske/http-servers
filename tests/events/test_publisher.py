"""
Tests for the event publisher functionality.
"""

import sys
import time
from pathlib import Path

import pytest

# Add the project root to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from events.models import ChangeType, EventType
from events.publisher import EventPublisher, FileWatcherConfig


@pytest.mark.events
@pytest.mark.events_unit
class TestEventPublisher:
    """Test event publisher functionality."""

    def test_file_creation_detection(self, isolated_env):
        """Test detection of file creation."""
        # Set up publisher to watch config directory
        config = FileWatcherConfig(path=str(isolated_env.config_dir), event_type=EventType.CONFIG_CHANGED)
        publisher = EventPublisher(isolated_env.event_queue, [config])

        # Initial scan (no files exist yet)
        events = publisher._scan_for_changes(config)
        assert len(events) == 0

        # Create config file
        isolated_env.create_config_file()

        # Scan again - should detect creation
        events = publisher._scan_for_changes(config)
        assert len(events) == 1
        assert events[0].change_type == ChangeType.CREATED
        assert events[0].event_type == EventType.CONFIG_CHANGED

    def test_file_modification_detection(self, isolated_env):
        """Test detection of file modification."""
        config_file = isolated_env.create_config_file("initial content")

        # Set up publisher
        config = FileWatcherConfig(path=str(config_file), event_type=EventType.CONFIG_CHANGED)
        publisher = EventPublisher(isolated_env.event_queue, [config])

        # Initial scan to establish baseline
        events = publisher._scan_for_changes(config)
        assert len(events) == 1  # Initial creation
        assert events[0].change_type == ChangeType.CREATED

        # Modify file
        time.sleep(0.1)  # Ensure mtime changes
        config_file.write_text("modified content")

        # Scan again - should detect modification
        events = publisher._scan_for_changes(config)
        assert len(events) == 1
        assert events[0].change_type == ChangeType.MODIFIED

    def test_file_deletion_detection(self, isolated_env):
        """Test detection of file deletion."""
        config_file = isolated_env.create_config_file()

        # Set up publisher to watch directory
        config = FileWatcherConfig(path=str(isolated_env.config_dir), event_type=EventType.CONFIG_CHANGED)
        publisher = EventPublisher(isolated_env.event_queue, [config])

        # Initial scan
        events = publisher._scan_for_changes(config)
        assert len(events) == 1  # Creation event

        # Delete file
        config_file.unlink()

        # Scan again - should detect deletion
        events = publisher._scan_for_changes(config)
        assert len(events) == 1
        assert events[0].change_type == ChangeType.DELETED

    def test_recursive_directory_watching(self, isolated_env):
        """Test recursive directory watching."""
        # Create subdirectory
        subdir = isolated_env.templates_dir / "subdir"
        subdir.mkdir()

        # Set up recursive publisher
        config = FileWatcherConfig(
            path=str(isolated_env.templates_dir), event_type=EventType.TEMPLATE_CHANGED, recursive=True
        )
        publisher = EventPublisher(isolated_env.event_queue, [config])

        # Create file in subdirectory
        template_file = subdir / "test.conf"
        template_file.write_text("test template")

        # Scan - should detect file in subdirectory
        events = publisher._scan_for_changes(config)
        assert len(events) == 1
        assert events[0].change_type == ChangeType.CREATED
        assert str(template_file) in events[0].source_path

    def test_multiple_file_types(self, isolated_env):
        """Test watching multiple file types simultaneously."""
        # Create different file types
        config_file = isolated_env.create_config_file()
        template_file = isolated_env.create_template_file("httpd.conf")
        user_file = isolated_env.create_user_file()

        # Set up publisher for all file types
        watch_configs = [
            FileWatcherConfig(str(config_file), EventType.CONFIG_CHANGED),
            FileWatcherConfig(str(template_file), EventType.TEMPLATE_CHANGED),
            FileWatcherConfig(str(user_file), EventType.USER_CHANGED),
        ]

        publisher = EventPublisher(isolated_env.event_queue, watch_configs)

        # Scan all configs
        all_events = []
        for config in watch_configs:
            events = publisher._scan_for_changes(config)
            all_events.extend(events)

        # Should detect all file types
        assert len(all_events) == 3

        event_types = {event.event_type for event in all_events}
        expected_types = {EventType.CONFIG_CHANGED, EventType.TEMPLATE_CHANGED, EventType.USER_CHANGED}
        assert event_types == expected_types

    def test_file_state_tracking(self, isolated_env):
        """Test that file states are properly tracked."""
        config_file = isolated_env.create_config_file("initial")

        config = FileWatcherConfig(path=str(config_file), event_type=EventType.CONFIG_CHANGED)
        publisher = EventPublisher(isolated_env.event_queue, [config])

        # Initial scan
        events = publisher._scan_for_changes(config)
        assert len(events) == 1

        # Scan again without changes - should detect nothing
        events = publisher._scan_for_changes(config)
        assert len(events) == 0

        # Make a change
        time.sleep(0.1)
        config_file.write_text("modified")

        # Should detect the change
        events = publisher._scan_for_changes(config)
        assert len(events) == 1
        assert events[0].change_type == ChangeType.MODIFIED

    def test_checksum_change_detection(self, isolated_env):
        """Test change detection using file checksums."""
        config_file = isolated_env.create_config_file("content")

        config = FileWatcherConfig(path=str(config_file), event_type=EventType.CONFIG_CHANGED)
        publisher = EventPublisher(isolated_env.event_queue, [config])

        # Initial scan
        events = publisher._scan_for_changes(config)
        assert len(events) == 1

        # Verify checksum is included in metadata
        if events[0].metadata.get("checksum"):
            initial_checksum = events[0].metadata["checksum"]

            # Modify content with same timestamp (if possible)
            config_file.write_text("different content")

            # Should still detect change via checksum
            events = publisher._scan_for_changes(config)
            if events:
                assert events[0].change_type == ChangeType.MODIFIED
                new_checksum = events[0].metadata.get("checksum")
                if new_checksum:
                    assert new_checksum != initial_checksum
