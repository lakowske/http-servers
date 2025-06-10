"""
Tests for event subscriber functionality.
"""

import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

# Add the project root to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from events.models import ChangeType, Event, EventResult, EventStatus, EventType
from events.subscriber import EventSubscriber, create_config_subscriber


@pytest.mark.events
@pytest.mark.events_unit
class TestEventSubscriber:
    """Test event subscriber functionality."""

    def test_event_processing(self, isolated_env):
        """Test processing events through subscriber."""
        # Create mock handler
        mock_handler = Mock()
        mock_handler.can_handle.return_value = True
        mock_handler.handle.return_value = EventResult(
            event_id="test-id", status=EventStatus.COMPLETED, message="Test success"
        )

        # Create subscriber
        subscriber = EventSubscriber(isolated_env.event_queue, [mock_handler])

        # Publish test event
        event = Event(
            event_type=EventType.CONFIG_CHANGED, source_path="/test/config.yaml", change_type=ChangeType.MODIFIED
        )
        isolated_env.event_queue.publish(event)

        # Process events
        processed = subscriber.process_events()

        # Verify processing
        assert processed == 1
        mock_handler.handle.assert_called_once()

        # Verify event completed
        stats = isolated_env.event_queue.get_queue_stats()
        assert stats["pending"] == 0
        assert stats["completed"] == 1

    def test_no_handler_available(self, isolated_env):
        """Test handling events with no available handler."""
        # Create subscriber with no handlers
        subscriber = EventSubscriber(isolated_env.event_queue, [])

        # Publish test event
        event = Event(
            event_type=EventType.CONFIG_CHANGED, source_path="/test/config.yaml", change_type=ChangeType.MODIFIED
        )
        isolated_env.event_queue.publish(event)

        # Process events
        processed = subscriber.process_events()

        # Verify processing occurred but failed
        assert processed == 1

        # Verify event marked as failed
        stats = isolated_env.event_queue.get_queue_stats()
        assert stats["pending"] == 0
        assert stats["failed"] == 1

    def test_handler_exception_handling(self, isolated_env):
        """Test handling of exceptions in event handlers."""
        # Create mock handler that raises exception
        mock_handler = Mock()
        mock_handler.can_handle.return_value = True
        mock_handler.handle.side_effect = Exception("Test error")

        subscriber = EventSubscriber(isolated_env.event_queue, [mock_handler])

        # Publish test event
        event = Event(
            event_type=EventType.CONFIG_CHANGED, source_path="/test/config.yaml", change_type=ChangeType.MODIFIED
        )
        isolated_env.event_queue.publish(event)

        # Process events
        processed = subscriber.process_events()

        # Verify processing occurred but failed
        assert processed == 1

        # Verify event marked as failed
        stats = isolated_env.event_queue.get_queue_stats()
        assert stats["pending"] == 0
        assert stats["failed"] == 1

    def test_multiple_handlers(self, isolated_env):
        """Test subscriber with multiple handlers."""
        # Create handlers for different event types
        config_handler = Mock()
        config_handler.can_handle.side_effect = lambda e: e.event_type == EventType.CONFIG_CHANGED
        config_handler.handle.return_value = EventResult(event_id="config", status=EventStatus.COMPLETED)

        template_handler = Mock()
        template_handler.can_handle.side_effect = lambda e: e.event_type == EventType.TEMPLATE_CHANGED
        template_handler.handle.return_value = EventResult(event_id="template", status=EventStatus.COMPLETED)

        subscriber = EventSubscriber(isolated_env.event_queue, [config_handler, template_handler])

        # Publish different event types
        events = [
            Event(
                event_type=EventType.CONFIG_CHANGED, source_path="/test/config.yaml", change_type=ChangeType.MODIFIED
            ),
            Event(
                event_type=EventType.TEMPLATE_CHANGED,
                source_path="/test/template.conf",
                change_type=ChangeType.MODIFIED,
            ),
        ]

        for event in events:
            isolated_env.event_queue.publish(event)

        # Process events
        processed = subscriber.process_events()

        # Verify both events processed
        assert processed == 2
        config_handler.handle.assert_called_once()
        template_handler.handle.assert_called_once()

    def test_event_batching(self, isolated_env):
        """Test processing events in batches."""
        mock_handler = Mock()
        mock_handler.can_handle.return_value = True
        mock_handler.handle.return_value = EventResult(event_id="test", status=EventStatus.COMPLETED)

        subscriber = EventSubscriber(isolated_env.event_queue, [mock_handler])

        # Publish many events
        for i in range(15):
            event = Event(
                event_type=EventType.CONFIG_CHANGED,
                source_path=f"/test/config{i}.yaml",
                change_type=ChangeType.MODIFIED,
            )
            isolated_env.event_queue.publish(event)

        # Process with batch limit
        processed = subscriber.process_events(max_events=5)

        # Should only process 5 events
        assert processed == 5
        assert mock_handler.handle.call_count == 5

        # Remaining events should still be pending
        stats = isolated_env.event_queue.get_queue_stats()
        assert stats["pending"] == 10

    def test_handler_management(self, isolated_env):
        """Test adding and removing handlers."""
        subscriber = EventSubscriber(isolated_env.event_queue, [])

        # Initially no handlers
        assert len(subscriber.handlers) == 0

        # Add handler
        mock_handler = Mock()
        subscriber.add_handler(mock_handler)
        assert len(subscriber.handlers) == 1
        assert mock_handler in subscriber.handlers

        # Remove handler
        subscriber.remove_handler(mock_handler)
        assert len(subscriber.handlers) == 0
        assert mock_handler not in subscriber.handlers

    def test_subscriber_lifecycle(self, isolated_env):
        """Test subscriber start/stop functionality."""
        subscriber = EventSubscriber(isolated_env.event_queue, [])

        # Initially running
        assert subscriber.running

        # Stop subscriber
        subscriber.stop()
        assert not subscriber.running

        # Processing should respect running state
        processed = subscriber.process_events()
        assert processed == 0  # Should not process when stopped


@pytest.mark.events
@pytest.mark.events_unit
class TestSubscriberFactory:
    """Test subscriber factory functions."""

    def test_create_config_subscriber(self, isolated_env):
        """Test creating a pre-configured subscriber."""
        mock_config_service = Mock()
        mock_render_callback = Mock()
        mock_reload_callback = Mock()
        mock_regenerate_callback = Mock()

        subscriber = create_config_subscriber(
            isolated_env.event_queue,
            config_service=mock_config_service,
            render_callback=mock_render_callback,
            reload_callback=mock_reload_callback,
            regenerate_callback=mock_regenerate_callback,
        )

        # Should have handlers for all event types
        assert len(subscriber.handlers) == 3

        # Test that handlers can handle their respective event types
        config_event = Event(
            event_type=EventType.CONFIG_CHANGED, source_path="/test/config.yaml", change_type=ChangeType.MODIFIED
        )

        template_event = Event(
            event_type=EventType.TEMPLATE_CHANGED, source_path="/test/template.conf", change_type=ChangeType.MODIFIED
        )

        user_event = Event(
            event_type=EventType.USER_CHANGED, source_path="/test/users.json", change_type=ChangeType.MODIFIED
        )

        # Find handlers that can handle each event type
        config_handlers = [h for h in subscriber.handlers if h.can_handle(config_event)]
        template_handlers = [h for h in subscriber.handlers if h.can_handle(template_event)]
        user_handlers = [h for h in subscriber.handlers if h.can_handle(user_event)]

        assert len(config_handlers) == 1
        assert len(template_handlers) == 1
        assert len(user_handlers) == 1

    def test_create_minimal_subscriber(self, isolated_env):
        """Test creating subscriber with minimal configuration."""
        subscriber = create_config_subscriber(isolated_env.event_queue)

        # Should still have handlers even without callbacks
        assert len(subscriber.handlers) == 3

        # Should be able to process events (with no-op behavior)
        event = Event(
            event_type=EventType.CONFIG_CHANGED, source_path="/test/config.yaml", change_type=ChangeType.MODIFIED
        )
        isolated_env.event_queue.publish(event)

        processed = subscriber.process_events()
        assert processed == 1

        # Event should complete successfully
        stats = isolated_env.event_queue.get_queue_stats()
        assert stats["completed"] == 1
