"""
Event system data models and types.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Types of events that can be published."""

    CONFIG_CHANGED = "config_changed"
    TEMPLATE_CHANGED = "template_changed"
    USER_CHANGED = "user_changed"
    CERTIFICATE_CHANGED = "certificate_changed"


class ChangeType(str, Enum):
    """Types of file system changes."""

    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"


class EventStatus(str, Enum):
    """Event processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Event(BaseModel):
    """Base event model."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: EventType
    source_path: str
    change_type: ChangeType
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EventResult(BaseModel):
    """Result of event processing."""

    event_id: str
    status: EventStatus
    message: Optional[str] = None
    error: Optional[str] = None
    processed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
