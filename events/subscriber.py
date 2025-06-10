"""
Event subscriber that processes events from the event queue.

Provides base classes and implementations for handling different types
of configuration change events.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import List, Optional

from .models import Event, EventResult, EventStatus, EventType
from .queue import EventQueue

logger = logging.getLogger(__name__)


class EventHandler(ABC):
    """Abstract base class for event handlers."""

    @abstractmethod
    def can_handle(self, event: Event) -> bool:
        """Check if this handler can process the given event.

        Args:
            event: Event to check

        Returns:
            True if handler can process event
        """

    @abstractmethod
    def handle(self, event: Event) -> EventResult:
        """Handle the event.

        Args:
            event: Event to handle

        Returns:
            Result of event processing
        """


class ConfigChangeHandler(EventHandler):
    """Handler for configuration file changes."""

    def __init__(self, config_service=None, render_callback=None):
        """Initialize config change handler.

        Args:
            config_service: Service for loading configuration
            render_callback: Callback to render configuration templates
        """
        self.config_service = config_service
        self.render_callback = render_callback

    def can_handle(self, event: Event) -> bool:
        """Check if this is a config change event."""
        return event.event_type == EventType.CONFIG_CHANGED

    def handle(self, event: Event) -> EventResult:
        """Handle configuration change.

        Args:
            event: Configuration change event

        Returns:
            Event processing result
        """
        try:
            logger.info(f"Processing config change: {event.source_path}")

            # Validate configuration if service available
            if self.config_service:
                try:
                    self.config_service.load_yaml_config(event.source_path)
                    logger.info("Configuration validation passed")
                except Exception as e:
                    logger.error(f"Configuration validation failed: {e}")
                    return EventResult(
                        event_id=event.id, status=EventStatus.FAILED, error=f"Configuration validation failed: {e}"
                    )

            # Render templates if callback available
            if self.render_callback:
                try:
                    self.render_callback()
                    logger.info("Configuration templates rendered successfully")
                except Exception as e:
                    logger.error(f"Template rendering failed: {e}")
                    return EventResult(
                        event_id=event.id, status=EventStatus.FAILED, error=f"Template rendering failed: {e}"
                    )

            return EventResult(
                event_id=event.id, status=EventStatus.COMPLETED, message="Configuration change processed successfully"
            )

        except Exception as e:
            logger.error(f"Error handling config change event {event.id}: {e}")
            return EventResult(event_id=event.id, status=EventStatus.FAILED, error=str(e))


class TemplateChangeHandler(EventHandler):
    """Handler for template file changes."""

    def __init__(self, render_callback=None, reload_callback=None):
        """Initialize template change handler.

        Args:
            render_callback: Callback to render templates
            reload_callback: Callback to reload affected services
        """
        self.render_callback = render_callback
        self.reload_callback = reload_callback

    def can_handle(self, event: Event) -> bool:
        """Check if this is a template change event."""
        return event.event_type == EventType.TEMPLATE_CHANGED

    def handle(self, event: Event) -> EventResult:
        """Handle template change.

        Args:
            event: Template change event

        Returns:
            Event processing result
        """
        try:
            logger.info(f"Processing template change: {event.source_path}")

            # Render templates if callback available
            if self.render_callback:
                try:
                    self.render_callback()
                    logger.info("Templates rendered successfully")
                except Exception as e:
                    logger.error(f"Template rendering failed: {e}")
                    return EventResult(
                        event_id=event.id, status=EventStatus.FAILED, error=f"Template rendering failed: {e}"
                    )

            # Reload affected services if callback available
            if self.reload_callback:
                try:
                    affected_services = self._determine_affected_services(event.source_path)
                    self.reload_callback(affected_services)
                    logger.info(f"Reloaded services: {affected_services}")
                except Exception as e:
                    logger.error(f"Service reload failed: {e}")
                    return EventResult(
                        event_id=event.id, status=EventStatus.FAILED, error=f"Service reload failed: {e}"
                    )

            return EventResult(
                event_id=event.id, status=EventStatus.COMPLETED, message="Template change processed successfully"
            )

        except Exception as e:
            logger.error(f"Error handling template change event {event.id}: {e}")
            return EventResult(event_id=event.id, status=EventStatus.FAILED, error=str(e))

    def _determine_affected_services(self, template_path: str) -> List[str]:
        """Determine which services are affected by template change.

        Args:
            template_path: Path to changed template

        Returns:
            List of service names that need reloading
        """
        template_name = template_path.lower()
        affected = []

        # HTTP service templates
        if any(name in template_name for name in ["httpd", "apache", "ssl", "git"]):
            affected.append("httpd")

        # Mail service templates
        if any(name in template_name for name in ["postfix", "dovecot", "mail"]):
            affected.append("mail")

        # Default to both if unclear
        if not affected:
            affected = ["httpd", "mail"]

        return affected


class UserChangeHandler(EventHandler):
    """Handler for user file changes."""

    def __init__(self, regenerate_callback=None):
        """Initialize user change handler.

        Args:
            regenerate_callback: Callback to regenerate auth files
        """
        self.regenerate_callback = regenerate_callback

    def can_handle(self, event: Event) -> bool:
        """Check if this is a user change event."""
        return event.event_type == EventType.USER_CHANGED

    def handle(self, event: Event) -> EventResult:
        """Handle user change.

        Args:
            event: User change event

        Returns:
            Event processing result
        """
        try:
            logger.info(f"Processing user change: {event.source_path}")

            # Regenerate auth files if callback available
            if self.regenerate_callback:
                try:
                    self.regenerate_callback(event.source_path)
                    logger.info("User authentication files regenerated")
                except Exception as e:
                    logger.error(f"User auth regeneration failed: {e}")
                    return EventResult(
                        event_id=event.id, status=EventStatus.FAILED, error=f"User auth regeneration failed: {e}"
                    )

            return EventResult(
                event_id=event.id, status=EventStatus.COMPLETED, message="User change processed successfully"
            )

        except Exception as e:
            logger.error(f"Error handling user change event {event.id}: {e}")
            return EventResult(event_id=event.id, status=EventStatus.FAILED, error=str(e))


class EventSubscriber:
    """Processes events from event queue using registered handlers."""

    def __init__(self, event_queue: EventQueue, handlers: Optional[List[EventHandler]] = None):
        """Initialize event subscriber.

        Args:
            event_queue: Event queue to process
            handlers: List of event handlers
        """
        self.event_queue = event_queue
        self.handlers = handlers or []
        self.running = True

    def add_handler(self, handler: EventHandler) -> None:
        """Add an event handler.

        Args:
            handler: Event handler to add
        """
        self.handlers.append(handler)

    def remove_handler(self, handler: EventHandler) -> None:
        """Remove an event handler.

        Args:
            handler: Event handler to remove
        """
        if handler in self.handlers:
            self.handlers.remove(handler)

    def stop(self) -> None:
        """Stop the subscriber."""
        self.running = False

    def process_events(self, max_events: int = 10) -> int:
        """Process pending events.

        Args:
            max_events: Maximum number of events to process in one batch

        Returns:
            Number of events processed
        """
        processed_count = 0

        try:
            pending_events = self.event_queue.get_pending_events()

            for event in pending_events[:max_events]:
                if not self.running:
                    break

                try:
                    # Claim the event for processing
                    if not self.event_queue.claim_event(event):
                        logger.warning(f"Failed to claim event {event.id}")
                        continue

                    # Find handler for event
                    handler = self._find_handler(event)
                    if not handler:
                        logger.warning(f"No handler found for event {event.id} type {event.event_type}")
                        result = EventResult(event_id=event.id, status=EventStatus.FAILED, error="No handler available")
                    else:
                        # Process event with timeout
                        result = handler.handle(event)

                    # Mark event as completed
                    self.event_queue.complete_event(event.id, result)
                    processed_count += 1

                    logger.debug(f"Processed event {event.id} with status {result.status}")

                except Exception as e:
                    logger.error(f"Error processing event {event.id}: {e}")
                    # Mark as failed
                    try:
                        result = EventResult(event_id=event.id, status=EventStatus.FAILED, error=str(e))
                        self.event_queue.complete_event(event.id, result)
                        processed_count += 1
                    except Exception as complete_error:
                        logger.error(f"Failed to mark event {event.id} as failed: {complete_error}")

        except Exception as e:
            logger.error(f"Error in process_events: {e}")

        return processed_count

    def run(self, poll_interval: float = 5.0, max_events_per_batch: int = 10) -> None:
        """Run the event subscriber in a loop.

        Args:
            poll_interval: Interval between checking for events
            max_events_per_batch: Maximum events to process per batch
        """
        logger.info("Starting event subscriber")

        while self.running:
            try:
                processed = self.process_events(max_events_per_batch)

                if processed > 0:
                    logger.info(f"Processed {processed} events")

                # Clean up old events periodically
                self.event_queue.cleanup_old_events()

                time.sleep(poll_interval)

            except Exception as e:
                logger.error(f"Error in subscriber run loop: {e}")
                time.sleep(poll_interval)

        logger.info("Event subscriber stopped")

    def _find_handler(self, event: Event) -> Optional[EventHandler]:
        """Find a handler that can process the given event.

        Args:
            event: Event to find handler for

        Returns:
            Event handler or None if not found
        """
        for handler in self.handlers:
            try:
                if handler.can_handle(event):
                    return handler
            except Exception as e:
                logger.error(f"Error checking if handler can handle event {event.id}: {e}")

        return None


def create_config_subscriber(
    event_queue: EventQueue, config_service=None, render_callback=None, reload_callback=None, regenerate_callback=None
) -> EventSubscriber:
    """Create a pre-configured event subscriber for configuration events.

    Args:
        event_queue: Event queue to subscribe to
        config_service: Configuration service for validation
        render_callback: Callback for rendering templates
        reload_callback: Callback for reloading services
        regenerate_callback: Callback for regenerating auth files

    Returns:
        Configured event subscriber
    """
    handlers = [
        ConfigChangeHandler(config_service, render_callback),
        TemplateChangeHandler(render_callback, reload_callback),
        UserChangeHandler(regenerate_callback),
    ]

    return EventSubscriber(event_queue, handlers)
