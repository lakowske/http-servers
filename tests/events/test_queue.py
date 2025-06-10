"""
Tests for the event queue functionality.
"""

import sys
from pathlib import Path

import pytest

# Ensure we can import the events module
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from events import ChangeType, Event, EventResult, EventStatus, EventType


@pytest.mark.events
@pytest.mark.events_unit
class TestEventQueue:
    """Test event queue functionality."""

    def test_event_publishing_and_retrieval(self, isolated_env):
        """Test publishing and retrieving events."""
        # Create test event
        event = Event(
            event_type=EventType.CONFIG_CHANGED, source_path="/test/config.yaml", change_type=ChangeType.MODIFIED
        )

        # Publish event
        isolated_env.event_queue.publish(event)

        # Retrieve pending events
        pending = isolated_env.event_queue.get_pending_events()
        assert len(pending) == 1
        assert pending[0].id == event.id
        assert pending[0].event_type == EventType.CONFIG_CHANGED

    def test_event_claim_and_complete(self, isolated_env):
        """Test claiming and completing events."""
        # Create and publish event
        event = Event(
            event_type=EventType.TEMPLATE_CHANGED, source_path="/test/template.conf", change_type=ChangeType.CREATED
        )
        isolated_env.event_queue.publish(event)

        # Claim event
        pending = isolated_env.event_queue.get_pending_events()
        assert isolated_env.event_queue.claim_event(pending[0])

        # Verify event moved to processing
        stats = isolated_env.event_queue.get_queue_stats()
        assert stats["pending"] == 0
        assert stats["processing"] == 1

        # Complete event
        result = EventResult(event_id=event.id, status=EventStatus.COMPLETED, message="Test completion")
        isolated_env.event_queue.complete_event(event.id, result)

        # Verify event moved to completed
        stats = isolated_env.event_queue.get_queue_stats()
        assert stats["processing"] == 0
        assert stats["completed"] == 1

    def test_queue_cleanup(self, isolated_env):
        """Test cleaning up old events."""
        # Create multiple events
        for i in range(5):
            event = Event(
                event_type=EventType.CONFIG_CHANGED,
                source_path=f"/test/config{i}.yaml",
                change_type=ChangeType.MODIFIED,
            )
            isolated_env.event_queue.publish(event)

            # Complete immediately
            isolated_env.event_queue.claim_event(event)
            result = EventResult(event_id=event.id, status=EventStatus.COMPLETED)
            isolated_env.event_queue.complete_event(event.id, result)

        # Verify events are completed
        stats = isolated_env.event_queue.get_queue_stats()
        assert stats["completed"] == 5

        # Cleanup with very low limits
        isolated_env.event_queue.cleanup_old_events(max_age_hours=0, max_count=2)

        # Verify cleanup occurred
        stats = isolated_env.event_queue.get_queue_stats()
        assert stats["completed"] <= 2

    def test_atomic_operations(self, isolated_env):
        """Test that queue operations are atomic."""
        event = Event(
            event_type=EventType.CONFIG_CHANGED, source_path="/test/config.yaml", change_type=ChangeType.MODIFIED
        )

        # Publishing should be atomic
        isolated_env.event_queue.publish(event)

        # Event should appear immediately
        pending = isolated_env.event_queue.get_pending_events()
        assert len(pending) == 1

        # Claiming should be atomic
        assert isolated_env.event_queue.claim_event(pending[0])

        # Trying to claim again should fail
        assert not isolated_env.event_queue.claim_event(pending[0])

    def test_concurrent_event_processing(self, isolated_env):
        """Test handling multiple events concurrently."""
        events = []
        for i in range(10):
            event = Event(
                event_type=EventType.TEMPLATE_CHANGED,
                source_path=f"/test/template{i}.conf",
                change_type=ChangeType.MODIFIED,
            )
            isolated_env.event_queue.publish(event)
            events.append(event)

        # All events should be pending
        pending = isolated_env.event_queue.get_pending_events()
        assert len(pending) == 10

        # Claim and complete all events
        for event in pending:
            assert isolated_env.event_queue.claim_event(event)
            result = EventResult(event_id=event.id, status=EventStatus.COMPLETED)
            isolated_env.event_queue.complete_event(event.id, result)

        # All events should be completed
        stats = isolated_env.event_queue.get_queue_stats()
        assert stats["pending"] == 0
        assert stats["processing"] == 0
        assert stats["completed"] == 10
