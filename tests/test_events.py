"""
Host-based tests for the file event system.

These tests run entirely on the host system without requiring containers,
enabling fast development and CI/CD testing.
"""

import json
import shutil
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock

from events.models import ChangeType, Event, EventResult, EventStatus, EventType
from events.publisher import EventPublisher, FileWatcherConfig
from events.queue import EventQueue
from events.subscriber import (
    ConfigChangeHandler,
    EventSubscriber,
    TemplateChangeHandler,
    UserChangeHandler,
    create_config_subscriber,
)


class IsolatedTestEnvironment:
    """Creates isolated test environment with temp directories."""

    def __init__(self):
        """Initialize isolated test environment."""
        self.temp_dir = None
        self.queue_dir = None
        self.config_dir = None
        self.templates_dir = None
        self.event_queue = None

    def __enter__(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp(prefix="events_test_"))
        self.queue_dir = self.temp_dir / "events"
        self.config_dir = self.temp_dir / "secrets"
        self.templates_dir = self.temp_dir / "templates"

        # Create directories
        self.queue_dir.mkdir()
        self.config_dir.mkdir()
        self.templates_dir.mkdir()

        # Create event queue
        self.event_queue = EventQueue(str(self.queue_dir))

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up test environment."""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def create_config_file(self, content: str = None) -> Path:
        """Create a test configuration file.

        Args:
            content: File content (default YAML config)

        Returns:
            Path to created file
        """
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
        """Create a test template file.

        Args:
            name: Template filename
            content: Template content

        Returns:
            Path to created file
        """
        template_file = self.templates_dir / name
        template_file.write_text(content)
        return template_file

    def create_user_file(self, content: str = None) -> Path:
        """Create a test user file.

        Args:
            content: File content (default JSON)

        Returns:
            Path to created file
        """
        if content is None:
            content = json.dumps({"users": [{"username": "testuser", "password": "testpass"}]})

        user_file = self.config_dir / "unified_users.json"
        user_file.write_text(content)
        return user_file


class TestEventQueue(unittest.TestCase):
    """Test event queue functionality."""

    def test_event_publishing_and_retrieval(self):
        """Test publishing and retrieving events."""
        with IsolatedTestEnvironment() as env:
            # Create test event
            event = Event(
                event_type=EventType.CONFIG_CHANGED, source_path="/test/config.yaml", change_type=ChangeType.MODIFIED
            )

            # Publish event
            env.event_queue.publish(event)

            # Retrieve pending events
            pending = env.event_queue.get_pending_events()
            self.assertEqual(len(pending), 1)
            self.assertEqual(pending[0].id, event.id)
            self.assertEqual(pending[0].event_type, EventType.CONFIG_CHANGED)

    def test_event_claim_and_complete(self):
        """Test claiming and completing events."""
        with IsolatedTestEnvironment() as env:
            # Create and publish event
            event = Event(
                event_type=EventType.TEMPLATE_CHANGED, source_path="/test/template.conf", change_type=ChangeType.CREATED
            )
            env.event_queue.publish(event)

            # Claim event
            pending = env.event_queue.get_pending_events()
            self.assertTrue(env.event_queue.claim_event(pending[0]))

            # Verify event moved to processing
            stats = env.event_queue.get_queue_stats()
            self.assertEqual(stats["pending"], 0)
            self.assertEqual(stats["processing"], 1)

            # Complete event
            result = EventResult(event_id=event.id, status=EventStatus.COMPLETED, message="Test completion")
            env.event_queue.complete_event(event.id, result)

            # Verify event moved to completed
            stats = env.event_queue.get_queue_stats()
            self.assertEqual(stats["processing"], 0)
            self.assertEqual(stats["completed"], 1)

    def test_queue_cleanup(self):
        """Test cleaning up old events."""
        with IsolatedTestEnvironment() as env:
            # Create multiple events
            for i in range(5):
                event = Event(
                    event_type=EventType.CONFIG_CHANGED,
                    source_path=f"/test/config{i}.yaml",
                    change_type=ChangeType.MODIFIED,
                )
                env.event_queue.publish(event)

                # Complete immediately
                env.event_queue.claim_event(event)
                result = EventResult(event_id=event.id, status=EventStatus.COMPLETED)
                env.event_queue.complete_event(event.id, result)

            # Verify events are completed
            stats = env.event_queue.get_queue_stats()
            self.assertEqual(stats["completed"], 5)

            # Cleanup with very low limits
            env.event_queue.cleanup_old_events(max_age_hours=0, max_count=2)

            # Verify cleanup occurred
            stats = env.event_queue.get_queue_stats()
            self.assertLessEqual(stats["completed"], 2)


class TestEventPublisher(unittest.TestCase):
    """Test event publisher functionality."""

    def test_file_creation_detection(self):
        """Test detection of file creation."""
        with IsolatedTestEnvironment() as env:
            # Set up publisher to watch config directory
            config = FileWatcherConfig(path=str(env.config_dir), event_type=EventType.CONFIG_CHANGED)
            publisher = EventPublisher(env.event_queue, [config])

            # Initial scan (no files exist yet)
            events = publisher._scan_for_changes(config)
            self.assertEqual(len(events), 0)

            # Create config file
            env.create_config_file()

            # Scan again - should detect creation
            events = publisher._scan_for_changes(config)
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].change_type, ChangeType.CREATED)
            self.assertEqual(events[0].event_type, EventType.CONFIG_CHANGED)

    def test_file_modification_detection(self):
        """Test detection of file modification."""
        with IsolatedTestEnvironment() as env:
            config_file = env.create_config_file("initial content")

            # Set up publisher
            config = FileWatcherConfig(path=str(config_file), event_type=EventType.CONFIG_CHANGED)
            publisher = EventPublisher(env.event_queue, [config])

            # Initial scan to establish baseline
            events = publisher._scan_for_changes(config)
            self.assertEqual(len(events), 1)  # Initial creation
            self.assertEqual(events[0].change_type, ChangeType.CREATED)

            # Modify file
            time.sleep(0.1)  # Ensure mtime changes
            config_file.write_text("modified content")

            # Scan again - should detect modification
            events = publisher._scan_for_changes(config)
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].change_type, ChangeType.MODIFIED)

    def test_file_deletion_detection(self):
        """Test detection of file deletion."""
        with IsolatedTestEnvironment() as env:
            config_file = env.create_config_file()

            # Set up publisher to watch directory
            config = FileWatcherConfig(path=str(env.config_dir), event_type=EventType.CONFIG_CHANGED)
            publisher = EventPublisher(env.event_queue, [config])

            # Initial scan
            events = publisher._scan_for_changes(config)
            self.assertEqual(len(events), 1)  # Creation event

            # Delete file
            config_file.unlink()

            # Scan again - should detect deletion
            events = publisher._scan_for_changes(config)
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].change_type, ChangeType.DELETED)

    def test_recursive_directory_watching(self):
        """Test recursive directory watching."""
        with IsolatedTestEnvironment() as env:
            # Create subdirectory
            subdir = env.templates_dir / "subdir"
            subdir.mkdir()

            # Set up recursive publisher
            config = FileWatcherConfig(
                path=str(env.templates_dir), event_type=EventType.TEMPLATE_CHANGED, recursive=True
            )
            publisher = EventPublisher(env.event_queue, [config])

            # Create file in subdirectory
            template_file = subdir / "test.conf"
            template_file.write_text("test template")

            # Scan - should detect file in subdirectory
            events = publisher._scan_for_changes(config)
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].change_type, ChangeType.CREATED)
            self.assertTrue(str(template_file) in events[0].source_path)


class TestEventHandlers(unittest.TestCase):
    """Test event handler functionality."""

    def test_config_change_handler(self):
        """Test configuration change handler."""
        # Mock config service
        mock_config_service = Mock()
        mock_render_callback = Mock()

        handler = ConfigChangeHandler(mock_config_service, mock_render_callback)

        # Create config change event
        event = Event(
            event_type=EventType.CONFIG_CHANGED, source_path="/test/config.yaml", change_type=ChangeType.MODIFIED
        )

        # Test handler can handle event
        self.assertTrue(handler.can_handle(event))

        # Handle event
        result = handler.handle(event)

        # Verify callbacks were called
        mock_config_service.load_yaml_config.assert_called_once_with("/test/config.yaml")
        mock_render_callback.assert_called_once()

        # Verify result
        self.assertEqual(result.event_id, event.id)
        self.assertEqual(result.status, EventStatus.COMPLETED)

    def test_template_change_handler(self):
        """Test template change handler."""
        mock_render_callback = Mock()
        mock_reload_callback = Mock()

        handler = TemplateChangeHandler(mock_render_callback, mock_reload_callback)

        # Create template change event
        event = Event(
            event_type=EventType.TEMPLATE_CHANGED, source_path="/templates/httpd.conf", change_type=ChangeType.MODIFIED
        )

        # Test handler can handle event
        self.assertTrue(handler.can_handle(event))

        # Handle event
        handler.handle(event)

        # Verify callbacks were called
        mock_render_callback.assert_called_once()
        mock_reload_callback.assert_called_once()

        # Verify affected services determination
        affected_services = handler._determine_affected_services("/templates/httpd.conf")
        self.assertIn("httpd", affected_services)

    def test_user_change_handler(self):
        """Test user change handler."""
        mock_regenerate_callback = Mock()

        handler = UserChangeHandler(mock_regenerate_callback)

        # Create user change event
        event = Event(
            event_type=EventType.USER_CHANGED,
            source_path="/secrets/unified_users.json",
            change_type=ChangeType.MODIFIED,
        )

        # Test handler can handle event
        self.assertTrue(handler.can_handle(event))

        # Handle event
        result = handler.handle(event)

        # Verify callback was called
        mock_regenerate_callback.assert_called_once_with("/secrets/unified_users.json")

        # Verify result
        self.assertEqual(result.event_id, event.id)
        self.assertEqual(result.status, EventStatus.COMPLETED)


class TestEventSubscriber(unittest.TestCase):
    """Test event subscriber functionality."""

    def test_event_processing(self):
        """Test processing events through subscriber."""
        with IsolatedTestEnvironment() as env:
            # Create mock handler
            mock_handler = Mock()
            mock_handler.can_handle.return_value = True
            mock_handler.handle.return_value = EventResult(
                event_id="test-id", status=EventStatus.COMPLETED, message="Test success"
            )

            # Create subscriber
            subscriber = EventSubscriber(env.event_queue, [mock_handler])

            # Publish test event
            event = Event(
                event_type=EventType.CONFIG_CHANGED, source_path="/test/config.yaml", change_type=ChangeType.MODIFIED
            )
            env.event_queue.publish(event)

            # Process events
            processed = subscriber.process_events()

            # Verify processing
            self.assertEqual(processed, 1)
            mock_handler.handle.assert_called_once()

            # Verify event completed
            stats = env.event_queue.get_queue_stats()
            self.assertEqual(stats["pending"], 0)
            self.assertEqual(stats["completed"], 1)

    def test_no_handler_available(self):
        """Test handling events with no available handler."""
        with IsolatedTestEnvironment() as env:
            # Create subscriber with no handlers
            subscriber = EventSubscriber(env.event_queue, [])

            # Publish test event
            event = Event(
                event_type=EventType.CONFIG_CHANGED, source_path="/test/config.yaml", change_type=ChangeType.MODIFIED
            )
            env.event_queue.publish(event)

            # Process events
            processed = subscriber.process_events()

            # Verify processing occurred but failed
            self.assertEqual(processed, 1)

            # Verify event marked as failed
            stats = env.event_queue.get_queue_stats()
            self.assertEqual(stats["pending"], 0)
            self.assertEqual(stats["failed"], 1)

    def test_handler_exception_handling(self):
        """Test handling of exceptions in event handlers."""
        with IsolatedTestEnvironment() as env:
            # Create mock handler that raises exception
            mock_handler = Mock()
            mock_handler.can_handle.return_value = True
            mock_handler.handle.side_effect = Exception("Test error")

            subscriber = EventSubscriber(env.event_queue, [mock_handler])

            # Publish test event
            event = Event(
                event_type=EventType.CONFIG_CHANGED, source_path="/test/config.yaml", change_type=ChangeType.MODIFIED
            )
            env.event_queue.publish(event)

            # Process events
            processed = subscriber.process_events()

            # Verify processing occurred but failed
            self.assertEqual(processed, 1)

            # Verify event marked as failed
            stats = env.event_queue.get_queue_stats()
            self.assertEqual(stats["pending"], 0)
            self.assertEqual(stats["failed"], 1)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete event system."""

    def test_end_to_end_config_change(self):
        """Test complete config change workflow."""
        with IsolatedTestEnvironment() as env:
            # Create mock callbacks
            mock_config_service = Mock()
            mock_render_callback = Mock()

            # Set up subscriber
            subscriber = create_config_subscriber(
                env.event_queue, config_service=mock_config_service, render_callback=mock_render_callback
            )

            # Set up publisher
            config = FileWatcherConfig(path=str(env.config_dir / "config.yaml"), event_type=EventType.CONFIG_CHANGED)
            publisher = EventPublisher(env.event_queue, [config])

            # Create initial config file
            env.create_config_file()

            # Scan for initial creation
            events = publisher._scan_for_changes(config)
            for event in events:
                env.event_queue.publish(event)

            # Process events
            processed = subscriber.process_events()
            self.assertGreater(processed, 0)

            # Verify config service was called
            mock_config_service.load_yaml_config.assert_called()
            mock_render_callback.assert_called()

    def test_multiple_event_types(self):
        """Test handling multiple different event types."""
        with IsolatedTestEnvironment() as env:
            # Create mock callbacks
            mock_config_service = Mock()
            mock_render_callback = Mock()
            mock_reload_callback = Mock()
            mock_regenerate_callback = Mock()

            # Set up subscriber
            subscriber = create_config_subscriber(
                env.event_queue,
                config_service=mock_config_service,
                render_callback=mock_render_callback,
                reload_callback=mock_reload_callback,
                regenerate_callback=mock_regenerate_callback,
            )

            # Create different types of events
            events = [
                Event(
                    event_type=EventType.CONFIG_CHANGED,
                    source_path="/test/config.yaml",
                    change_type=ChangeType.MODIFIED,
                ),
                Event(
                    event_type=EventType.TEMPLATE_CHANGED,
                    source_path="/templates/httpd.conf",
                    change_type=ChangeType.MODIFIED,
                ),
                Event(
                    event_type=EventType.USER_CHANGED,
                    source_path="/secrets/users.json",
                    change_type=ChangeType.MODIFIED,
                ),
            ]

            # Publish all events
            for event in events:
                env.event_queue.publish(event)

            # Process all events
            processed = subscriber.process_events(max_events=10)
            self.assertEqual(processed, 3)

            # Verify all callbacks were called
            mock_config_service.load_yaml_config.assert_called()
            mock_render_callback.assert_called()
            mock_reload_callback.assert_called()
            mock_regenerate_callback.assert_called()


if __name__ == "__main__":
    unittest.main()
