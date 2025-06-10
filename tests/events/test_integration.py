"""
Integration tests for the event system.

These tests verify end-to-end functionality and component integration.
"""

import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

# Add the project root to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from events.models import ChangeType, Event, EventType
from events.publisher import EventPublisher, FileWatcherConfig, create_config_publisher
from events.subscriber import create_config_subscriber


@pytest.mark.events
@pytest.mark.events_integration
class TestEventSystemIntegration:
    """Integration tests for the complete event system."""

    def test_end_to_end_config_change(self, isolated_env):
        """Test complete config change workflow."""
        # Create mock callbacks
        mock_config_service = Mock()
        mock_render_callback = Mock()

        # Set up subscriber
        subscriber = create_config_subscriber(
            isolated_env.event_queue, config_service=mock_config_service, render_callback=mock_render_callback
        )

        # Set up publisher
        config = FileWatcherConfig(
            path=str(isolated_env.config_dir / "config.yaml"), event_type=EventType.CONFIG_CHANGED
        )
        publisher = EventPublisher(isolated_env.event_queue, [config])

        # Create initial config file
        config_file = isolated_env.create_config_file()

        # Scan for initial creation
        events = publisher._scan_for_changes(config)
        for event in events:
            isolated_env.event_queue.publish(event)

        # Process events
        processed = subscriber.process_events()
        assert processed > 0

        # Verify config service was called
        mock_config_service.load_yaml_config.assert_called()
        mock_render_callback.assert_called()

    def test_multiple_event_types(self, isolated_env):
        """Test handling multiple different event types."""
        # Create mock callbacks
        mock_config_service = Mock()
        mock_render_callback = Mock()
        mock_reload_callback = Mock()
        mock_regenerate_callback = Mock()

        # Set up subscriber
        subscriber = create_config_subscriber(
            isolated_env.event_queue,
            config_service=mock_config_service,
            render_callback=mock_render_callback,
            reload_callback=mock_reload_callback,
            regenerate_callback=mock_regenerate_callback,
        )

        # Create different types of events
        events = [
            Event(
                event_type=EventType.CONFIG_CHANGED, source_path="/test/config.yaml", change_type=ChangeType.MODIFIED
            ),
            Event(
                event_type=EventType.TEMPLATE_CHANGED,
                source_path="/templates/httpd.conf",
                change_type=ChangeType.MODIFIED,
            ),
            Event(
                event_type=EventType.USER_CHANGED, source_path="/secrets/users.json", change_type=ChangeType.MODIFIED
            ),
        ]

        # Publish all events
        for event in events:
            isolated_env.event_queue.publish(event)

        # Process all events
        processed = subscriber.process_events(max_events=10)
        assert processed == 3

        # Verify all callbacks were called
        mock_config_service.load_yaml_config.assert_called()
        mock_render_callback.assert_called()
        mock_reload_callback.assert_called()
        mock_regenerate_callback.assert_called()

    def test_publisher_subscriber_coordination(self, isolated_env):
        """Test coordination between publisher and subscriber."""
        # Set up publisher with multiple file types
        config_file = isolated_env.create_config_file()
        template_file = isolated_env.create_template_file("httpd.conf")

        watch_configs = [
            FileWatcherConfig(str(config_file), EventType.CONFIG_CHANGED),
            FileWatcherConfig(str(template_file), EventType.TEMPLATE_CHANGED),
        ]

        publisher = EventPublisher(isolated_env.event_queue, watch_configs)

        # Track processing results
        processed_events = []

        def track_processing(path):
            processed_events.append(("config", path))

        def track_rendering():
            processed_events.append(("render", None))

        def track_reloading(services):
            processed_events.append(("reload", services))

        # Set up subscriber with tracking
        subscriber = create_config_subscriber(
            isolated_env.event_queue,
            config_service=Mock(load_yaml_config=track_processing),
            render_callback=track_rendering,
            reload_callback=track_reloading,
        )

        # Simulate file changes by scanning
        all_events = []
        for config in watch_configs:
            events = publisher._scan_for_changes(config)
            all_events.extend(events)
            for event in events:
                isolated_env.event_queue.publish(event)

        # Process all events
        processed = subscriber.process_events(max_events=10)
        assert processed == len(all_events)

        # Verify processing occurred
        assert len(processed_events) > 0

        # Verify queue is clean
        stats = isolated_env.event_queue.get_queue_stats()
        assert stats["pending"] == 0

    def test_error_recovery_integration(self, isolated_env):
        """Test error recovery in integrated system."""
        # Set up publisher
        config_file = isolated_env.create_config_file()
        config = FileWatcherConfig(str(config_file), EventType.CONFIG_CHANGED)
        publisher = EventPublisher(isolated_env.event_queue, [config])

        # Set up subscriber with failing callback
        failing_service = Mock()
        failing_service.load_yaml_config.side_effect = Exception("Validation failed")

        subscriber = create_config_subscriber(isolated_env.event_queue, config_service=failing_service)

        # Generate and publish events
        events = publisher._scan_for_changes(config)
        for event in events:
            isolated_env.event_queue.publish(event)

        # Process events (should handle failure gracefully)
        processed = subscriber.process_events()
        assert processed > 0

        # Verify events were marked as failed
        stats = isolated_env.event_queue.get_queue_stats()
        assert stats["failed"] > 0

    def test_high_volume_event_processing(self, isolated_env):
        """Test processing many events efficiently."""
        # Create many files to generate events
        template_files = []
        for i in range(20):
            template_file = isolated_env.create_template_file(f"template{i}.conf")
            template_files.append(template_file)

        # Set up publisher for template directory
        config = FileWatcherConfig(
            path=str(isolated_env.templates_dir), event_type=EventType.TEMPLATE_CHANGED, recursive=True
        )
        publisher = EventPublisher(isolated_env.event_queue, [config])

        # Set up subscriber with tracking
        processed_count = [0]  # Use list for closure modification

        def count_processing():
            processed_count[0] += 1

        subscriber = create_config_subscriber(isolated_env.event_queue, render_callback=count_processing)

        # Generate events for all files
        events = publisher._scan_for_changes(config)
        for event in events:
            isolated_env.event_queue.publish(event)

        # Process all events
        total_processed = subscriber.process_events(max_events=100)
        assert total_processed == len(events)
        assert processed_count[0] == len(events)

        # Verify all events completed
        stats = isolated_env.event_queue.get_queue_stats()
        assert stats["pending"] == 0
        assert stats["completed"] == len(events)

    def test_config_publisher_integration(self, isolated_env):
        """Test the pre-configured publisher integration."""
        # Create standard config files
        config_file = isolated_env.create_config_file()
        template_file = isolated_env.create_template_file("httpd.conf")
        user_file = isolated_env.create_user_file()

        # Use pre-configured publisher
        publisher = create_config_publisher(
            isolated_env.event_queue,
            config_dir=str(isolated_env.config_dir),
            templates_dir=str(isolated_env.templates_dir),
        )

        # Verify publisher has correct configurations
        assert len(publisher.watch_configs) == 3

        # Find config types
        config_types = {config.event_type for config in publisher.watch_configs}
        expected_types = {EventType.CONFIG_CHANGED, EventType.USER_CHANGED, EventType.TEMPLATE_CHANGED}
        assert config_types == expected_types

        # Test that it can detect changes
        all_events = []
        for config in publisher.watch_configs:
            events = publisher._scan_for_changes(config)
            all_events.extend(events)

        # Should detect all created files
        assert len(all_events) >= 3  # At least one for each file type

    def test_queue_persistence_integration(self, isolated_env):
        """Test that events persist across queue operations."""
        # Create events directly
        events = [
            Event(event_type=EventType.CONFIG_CHANGED, source_path="/test1.yaml", change_type=ChangeType.MODIFIED),
            Event(event_type=EventType.TEMPLATE_CHANGED, source_path="/test2.conf", change_type=ChangeType.MODIFIED),
        ]

        # Publish events
        for event in events:
            isolated_env.event_queue.publish(event)

        # Create new queue instance (simulating restart)
        new_queue = isolated_env.event_queue.__class__(str(isolated_env.queue_dir))

        # Events should still be there
        pending = new_queue.get_pending_events()
        assert len(pending) == 2

        # Process with new subscriber
        subscriber = create_config_subscriber(new_queue)
        processed = subscriber.process_events()
        assert processed == 2

        # Verify completion
        stats = new_queue.get_queue_stats()
        assert stats["completed"] == 2
