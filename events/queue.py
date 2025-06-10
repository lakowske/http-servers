"""
File-based event queue implementation.

Manages event lifecycle through filesystem directories for reliable
inter-process communication without external dependencies.
"""

import json
import logging
import os
import shutil
import time
from pathlib import Path
from typing import Iterator, List, Optional

from .models import Event, EventResult, EventStatus

logger = logging.getLogger(__name__)


class EventQueue:
    """File-based event queue using filesystem directories."""

    def __init__(self, queue_dir: str):
        """Initialize event queue.

        Args:
            queue_dir: Base directory for event queue
        """
        self.queue_dir = Path(queue_dir)
        self.pending_dir = self.queue_dir / "pending"
        self.processing_dir = self.queue_dir / "processing"
        self.completed_dir = self.queue_dir / "completed"
        self.failed_dir = self.queue_dir / "failed"

        # Create queue directories
        for directory in [self.pending_dir, self.processing_dir, self.completed_dir, self.failed_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def publish(self, event: Event) -> None:
        """Publish event to queue.

        Args:
            event: Event to publish
        """
        event_file = self.pending_dir / f"{event.id}.json"

        try:
            # Write event atomically using temp file + rename
            temp_file = event_file.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(event.dict(), f, indent=2, default=str)

            temp_file.rename(event_file)
            logger.debug(f"Published event {event.id} to queue")

        except Exception as e:
            logger.error(f"Failed to publish event {event.id}: {e}")
            # Clean up temp file if it exists
            if temp_file.exists():
                temp_file.unlink()
            raise

    def get_pending_events(self) -> List[Event]:
        """Get all pending events.

        Returns:
            List of pending events sorted by timestamp
        """
        events = []

        try:
            for event_file in self.pending_dir.glob("*.json"):
                try:
                    with open(event_file, "r", encoding="utf-8") as f:
                        event_data = json.load(f)

                    event = Event(**event_data)
                    events.append(event)

                except Exception as e:
                    logger.error(f"Failed to load event from {event_file}: {e}")
                    # Move corrupted event to failed directory
                    self._move_to_failed(event_file, f"Failed to parse: {e}")

            # Sort by timestamp
            events.sort(key=lambda e: e.timestamp)

        except Exception as e:
            logger.error(f"Failed to get pending events: {e}")

        return events

    def claim_event(self, event: Event) -> bool:
        """Claim an event for processing.

        Args:
            event: Event to claim

        Returns:
            True if event was successfully claimed, False otherwise
        """
        pending_file = self.pending_dir / f"{event.id}.json"
        processing_file = self.processing_dir / f"{event.id}.json"

        try:
            # Atomic move from pending to processing
            if pending_file.exists():
                shutil.move(str(pending_file), str(processing_file))
                logger.debug(f"Claimed event {event.id} for processing")
                return True
            else:
                logger.warning(f"Event {event.id} no longer pending")
                return False

        except Exception as e:
            logger.error(f"Failed to claim event {event.id}: {e}")
            return False

    def complete_event(self, event_id: str, result: EventResult) -> None:
        """Mark event as completed.

        Args:
            event_id: ID of completed event
            result: Processing result
        """
        processing_file = self.processing_dir / f"{event_id}.json"

        if result.status == EventStatus.COMPLETED:
            target_dir = self.completed_dir
        else:
            target_dir = self.failed_dir

        result_file = target_dir / f"{event_id}.json"

        try:
            # Write result file
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(result.dict(), f, indent=2, default=str)

            # Remove from processing
            if processing_file.exists():
                processing_file.unlink()

            logger.debug(f"Completed event {event_id} with status {result.status}")

        except Exception as e:
            logger.error(f"Failed to complete event {event_id}: {e}")
            raise

    def cleanup_old_events(self, max_age_hours: int = 24, max_count: int = 1000) -> None:
        """Clean up old completed/failed events.

        Args:
            max_age_hours: Maximum age of events to keep
            max_count: Maximum number of events to keep per directory
        """
        cutoff_time = time.time() - (max_age_hours * 3600)

        for directory in [self.completed_dir, self.failed_dir]:
            try:
                # Get all event files with timestamps
                event_files = []
                for event_file in directory.glob("*.json"):
                    try:
                        stat = event_file.stat()
                        event_files.append((event_file, stat.st_mtime))
                    except OSError:
                        continue

                # Sort by modification time (newest first)
                event_files.sort(key=lambda x: x[1], reverse=True)

                # Remove old files
                removed_count = 0
                for event_file, mtime in event_files:
                    # Keep recent files and limit total count
                    if mtime >= cutoff_time and removed_count < max_count:
                        continue

                    try:
                        event_file.unlink()
                        removed_count += 1
                    except OSError as e:
                        logger.warning(f"Failed to remove old event file {event_file}: {e}")

                if removed_count > 0:
                    logger.info(f"Cleaned up {removed_count} old events from {directory.name}")

            except Exception as e:
                logger.error(f"Failed to cleanup events in {directory}: {e}")

    def get_queue_stats(self) -> dict:
        """Get queue statistics.

        Returns:
            Dictionary with queue statistics
        """
        try:
            return {
                "pending": len(list(self.pending_dir.glob("*.json"))),
                "processing": len(list(self.processing_dir.glob("*.json"))),
                "completed": len(list(self.completed_dir.glob("*.json"))),
                "failed": len(list(self.failed_dir.glob("*.json"))),
            }
        except Exception as e:
            logger.error(f"Failed to get queue stats: {e}")
            return {"error": str(e)}

    def _move_to_failed(self, event_file: Path, error_message: str) -> None:
        """Move corrupted event file to failed directory.

        Args:
            event_file: Path to event file
            error_message: Error description
        """
        try:
            failed_file = self.failed_dir / event_file.name
            shutil.move(str(event_file), str(failed_file))

            # Write error information
            error_file = failed_file.with_suffix(".error")
            with open(error_file, "w", encoding="utf-8") as f:
                f.write(error_message)

        except Exception as e:
            logger.error(f"Failed to move corrupted event to failed directory: {e}")
