"""
Event publisher that monitors file changes and publishes events.

Extends the existing UserFileWatcher pattern to handle multiple file types
and publish structured events to the event queue.
"""

import hashlib
import logging
import os
import signal
import time
from pathlib import Path
from typing import Dict, List, Optional

from .models import ChangeType, Event, EventType
from .queue import EventQueue

logger = logging.getLogger(__name__)


class FileWatcherConfig:
    """Configuration for file watching."""

    def __init__(self, path: str, event_type: EventType, recursive: bool = False):
        """Initialize file watcher config.

        Args:
            path: File or directory path to watch
            event_type: Type of events to publish for this path
            recursive: Whether to watch subdirectories recursively
        """
        self.path = Path(path)
        self.event_type = event_type
        self.recursive = recursive


class EventPublisher:
    """Publishes file change events to event queue."""

    def __init__(self, event_queue: EventQueue, watch_configs: List[FileWatcherConfig]):
        """Initialize event publisher.

        Args:
            event_queue: Event queue to publish to
            watch_configs: List of file watching configurations
        """
        self.event_queue = event_queue
        self.watch_configs = watch_configs
        self.running = True

        # Track file states for change detection
        self.file_states: Dict[str, dict] = {}

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

    def _handle_signal(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down publisher")
        self.running = False

    def _get_file_state(self, file_path: Path) -> Optional[dict]:
        """Get current state of a file.

        Args:
            file_path: Path to file

        Returns:
            Dictionary with file state information or None if file doesn't exist
        """
        try:
            if not file_path.exists():
                return None

            stat = file_path.stat()

            # Only calculate checksum for small files to avoid performance issues
            checksum = None
            if stat.st_size < 1024 * 1024:  # 1MB limit
                try:
                    with open(file_path, "rb") as f:
                        checksum = hashlib.sha256(f.read()).hexdigest()
                except (OSError, IOError):
                    pass

            return {"size": stat.st_size, "mtime": stat.st_mtime, "checksum": checksum}

        except (OSError, IOError):
            return None

    def _detect_change_type(
        self, file_path: Path, old_state: Optional[dict], new_state: Optional[dict]
    ) -> Optional[ChangeType]:
        """Detect the type of change that occurred.

        Args:
            file_path: Path to file
            old_state: Previous file state
            new_state: Current file state

        Returns:
            Change type or None if no significant change
        """
        if old_state is None and new_state is not None:
            return ChangeType.CREATED
        elif old_state is not None and new_state is None:
            return ChangeType.DELETED
        elif old_state is not None and new_state is not None:
            # Check for meaningful changes
            if (
                old_state["mtime"] != new_state["mtime"]
                or old_state["size"] != new_state["size"]
                or (
                    old_state.get("checksum")
                    and new_state.get("checksum")
                    and old_state["checksum"] != new_state["checksum"]
                )
            ):
                return ChangeType.MODIFIED

        return None

    def _scan_for_changes(self, config: FileWatcherConfig) -> List[Event]:
        """Scan for changes in watched paths.

        Args:
            config: File watcher configuration

        Returns:
            List of events for detected changes
        """
        events = []

        try:
            if config.path.is_file():
                # Single file monitoring
                file_path = config.path
                old_state = self.file_states.get(str(file_path))
                new_state = self._get_file_state(file_path)

                change_type = self._detect_change_type(file_path, old_state, new_state)
                if change_type:
                    metadata = {}
                    if new_state:
                        metadata.update(new_state)

                    event = Event(
                        event_type=config.event_type,
                        source_path=str(file_path),
                        change_type=change_type,
                        metadata=metadata,
                    )
                    events.append(event)

                # Update state
                self.file_states[str(file_path)] = new_state

            elif config.path.is_dir():
                # Directory monitoring
                pattern = "**/*" if config.recursive else "*"

                for file_path in config.path.glob(pattern):
                    if file_path.is_file():
                        old_state = self.file_states.get(str(file_path))
                        new_state = self._get_file_state(file_path)

                        change_type = self._detect_change_type(file_path, old_state, new_state)
                        if change_type:
                            metadata = {}
                            if new_state:
                                metadata.update(new_state)

                            event = Event(
                                event_type=config.event_type,
                                source_path=str(file_path),
                                change_type=change_type,
                                metadata=metadata,
                            )
                            events.append(event)

                        # Update state
                        self.file_states[str(file_path)] = new_state

                # Clean up states for deleted files
                current_files = {str(p) for p in config.path.glob(pattern) if p.is_file()}
                old_files = {path for path in self.file_states.keys() if path.startswith(str(config.path))}

                for deleted_file in old_files - current_files:
                    event = Event(
                        event_type=config.event_type,
                        source_path=deleted_file,
                        change_type=ChangeType.DELETED,
                        metadata={},
                    )
                    events.append(event)
                    del self.file_states[deleted_file]

        except Exception as e:
            logger.error(f"Error scanning for changes in {config.path}: {e}")

        return events

    def _try_inotify_watch(self) -> bool:
        """Try to use inotify for efficient file watching.

        Returns:
            True if inotify is available and working, False otherwise
        """
        try:
            import inotify.adapters

            logger.info("Starting inotify-based file watching")

            # Set up watches for all configured paths
            i = inotify.adapters.Inotify()
            watch_dirs = set()

            for config in self.watch_configs:
                if config.path.is_file():
                    watch_dir = config.path.parent
                else:
                    watch_dir = config.path

                if str(watch_dir) not in watch_dirs:
                    i.add_watch(str(watch_dir))
                    watch_dirs.add(str(watch_dir))
                    logger.debug(f"Added inotify watch for {watch_dir}")

            # Initial scan to capture existing state
            for config in self.watch_configs:
                events = self._scan_for_changes(config)
                for event in events:
                    self.event_queue.publish(event)

            # Process inotify events
            for event in i.event_gen(yield_nesting_events=True):
                if not self.running:
                    break

                if event is not None:
                    (_, type_names, path, filename) = event

                    # Check for relevant events
                    relevant_events = {"IN_MODIFY", "IN_MOVED_TO", "IN_CREATE", "IN_DELETE", "IN_CLOSE_WRITE"}
                    if any(event_type in relevant_events for event_type in type_names):
                        # Find matching configuration
                        file_path = Path(path) / filename if filename else Path(path)

                        for config in self.watch_configs:
                            if self._path_matches_config(file_path, config):
                                # Re-scan this specific configuration
                                events = self._scan_for_changes(config)
                                for change_event in events:
                                    self.event_queue.publish(change_event)
                                break

            return True

        except ImportError:
            logger.warning("inotify library not available, falling back to polling")
            return False
        except Exception as e:
            logger.error(f"Error with inotify watching: {e}")
            return False

    def _path_matches_config(self, file_path: Path, config: FileWatcherConfig) -> bool:
        """Check if a file path matches a watch configuration.

        Args:
            file_path: File path to check
            config: Watch configuration

        Returns:
            True if path matches configuration
        """
        try:
            if config.path.is_file():
                return file_path == config.path
            elif config.path.is_dir():
                if config.recursive:
                    return file_path.is_relative_to(config.path)
                else:
                    return file_path.parent == config.path
        except (OSError, ValueError):
            pass

        return False

    def _polling_watch(self, poll_interval: int = 5) -> None:
        """Watch files using polling as fallback.

        Args:
            poll_interval: Polling interval in seconds
        """
        logger.info(f"Starting polling-based file watching ({poll_interval}s interval)")

        # Initial scan
        for config in self.watch_configs:
            events = self._scan_for_changes(config)
            for event in events:
                self.event_queue.publish(event)

        # Polling loop
        while self.running:
            try:
                time.sleep(poll_interval)

                for config in self.watch_configs:
                    events = self._scan_for_changes(config)
                    for event in events:
                        self.event_queue.publish(event)

            except Exception as e:
                logger.error(f"Error in polling watch: {e}")
                time.sleep(poll_interval)

    def start_watching(self, use_polling: bool = False, poll_interval: int = 5) -> None:
        """Start watching for file changes.

        Args:
            use_polling: Force use of polling instead of inotify
            poll_interval: Polling interval in seconds
        """
        logger.info(f"Starting event publisher with {len(self.watch_configs)} watch configs")

        for config in self.watch_configs:
            logger.info(f"Watching {config.path} for {config.event_type} events")

        try:
            if not use_polling and self._try_inotify_watch():
                logger.info("inotify watching completed")
            else:
                self._polling_watch(poll_interval)
        finally:
            logger.info("Event publisher stopped")


def create_config_publisher(
    event_queue: EventQueue, config_dir: str = "secrets", templates_dir: str = "templates"
) -> EventPublisher:
    """Create a pre-configured event publisher for standard config files.

    Args:
        event_queue: Event queue to publish to
        config_dir: Directory containing configuration files
        templates_dir: Directory containing template files

    Returns:
        Configured event publisher
    """
    watch_configs = [
        FileWatcherConfig(path=os.path.join(config_dir, "config.yaml"), event_type=EventType.CONFIG_CHANGED),
        FileWatcherConfig(path=os.path.join(config_dir, "unified_users.json"), event_type=EventType.USER_CHANGED),
        FileWatcherConfig(path=templates_dir, event_type=EventType.TEMPLATE_CHANGED, recursive=True),
    ]

    return EventPublisher(event_queue, watch_configs)
