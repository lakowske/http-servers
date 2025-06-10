"""
File-based event system for configuration change notifications.

This package provides a lightweight, filesystem-based event system that enables
containers and host processes to communicate configuration changes without
requiring network communication or container restarts.

Key Components:
- EventPublisher: Publishes file change events to filesystem queue
- EventSubscriber: Consumes events from filesystem queue
- FileWatcher: Monitors file/directory changes using inotify/polling
- EventQueue: Manages event lifecycle through filesystem directories
"""

from .models import ChangeType, Event, EventResult, EventStatus, EventType
from .publisher import EventPublisher, FileWatcherConfig, create_config_publisher
from .queue import EventQueue
from .subscriber import EventSubscriber, create_config_subscriber

__all__ = [
    "Event",
    "EventResult",
    "EventStatus",
    "EventType",
    "ChangeType",
    "EventQueue",
    "EventPublisher",
    "FileWatcherConfig",
    "create_config_publisher",
    "EventSubscriber",
    "create_config_subscriber",
]
