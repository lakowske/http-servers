#!/usr/local/venv/bin/python
"""
Script to watch for changes to unified users JSON file and trigger config regeneration.
Runs inside containers using inotify.
"""

import os
import sys
import time
import subprocess
import logging
import signal
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class UserFileWatcher:
    """Watch for changes to unified users file and trigger regeneration."""

    def __init__(self, users_file: str, regenerate_script: str):
        self.users_file = users_file
        self.regenerate_script = regenerate_script
        self.running = True

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

    def _handle_signal(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down watcher")
        self.running = False

    def _trigger_regeneration(self):
        """Trigger config regeneration."""
        try:
            logger.info(f"Users file changed, triggering regeneration: {self.regenerate_script}")

            # Run the regeneration script
            result = subprocess.run([
                self.regenerate_script, self.users_file
            ], capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                logger.info("Config regeneration completed successfully")
                if result.stdout:
                    logger.info(f"Regeneration output: {result.stdout}")
            else:
                logger.error(f"Config regeneration failed with exit code {result.returncode}")
                if result.stderr:
                    logger.error(f"Regeneration error: {result.stderr}")

        except subprocess.TimeoutExpired:
            logger.error("Config regeneration timed out")
        except Exception as e:
            logger.error(f"Error triggering regeneration: {e}")

    def _wait_for_file(self):
        """Wait for the users file to exist."""
        while self.running and not os.path.exists(self.users_file):
            logger.info(f"Waiting for users file to be created: {self.users_file}")
            time.sleep(5)

        if os.path.exists(self.users_file):
            logger.info(f"Users file found: {self.users_file}")
            # Trigger initial regeneration
            self._trigger_regeneration()

    def watch_with_inotify(self):
        """Watch file using inotify (if available)."""
        try:
            import inotify.adapters

            # Watch the directory containing the file
            watch_dir = os.path.dirname(self.users_file)
            watch_filename = os.path.basename(self.users_file)

            logger.info(f"Starting inotify watch on {watch_dir} for file {watch_filename}")

            i = inotify.adapters.Inotify()
            i.add_watch(watch_dir)

            for event in i.event_gen(yield_nesting_events=True):
                if not self.running:
                    break

                if event is not None:
                    (_, type_names, path, filename) = event

                    # Check if this is our target file
                    if filename == watch_filename:
                        # Check for relevant events (modify, move, create)
                        relevant_events = {'IN_MODIFY', 'IN_MOVED_TO', 'IN_CREATE', 'IN_CLOSE_WRITE'}
                        if any(event_type in relevant_events for event_type in type_names):
                            logger.info(f"Detected change to {filename}: {type_names}")
                            self._trigger_regeneration()

        except ImportError:
            logger.warning("inotify library not available, falling back to polling")
            return False
        except Exception as e:
            logger.error(f"Error with inotify watching: {e}")
            return False

        return True

    def watch_with_polling(self, poll_interval: int = 5):
        """Watch file using polling as fallback."""
        logger.info(f"Starting polling watch with {poll_interval}s interval")

        last_mtime = 0
        if os.path.exists(self.users_file):
            last_mtime = os.path.getmtime(self.users_file)
            # Trigger initial regeneration
            self._trigger_regeneration()

        while self.running:
            try:
                time.sleep(poll_interval)

                if not os.path.exists(self.users_file):
                    if last_mtime > 0:
                        logger.warning(f"Users file disappeared: {self.users_file}")
                        last_mtime = 0
                    continue

                current_mtime = os.path.getmtime(self.users_file)

                if current_mtime > last_mtime:
                    logger.info(f"Users file modified (mtime: {current_mtime})")
                    last_mtime = current_mtime
                    self._trigger_regeneration()

            except Exception as e:
                logger.error(f"Error in polling watch: {e}")
                time.sleep(poll_interval)

    def start_watching(self, use_polling: bool = False, poll_interval: int = 5):
        """Start watching for file changes."""
        logger.info(f"Starting user file watcher for: {self.users_file}")
        logger.info(f"Regeneration script: {self.regenerate_script}")

        # Wait for file to exist initially
        self._wait_for_file()

        if not self.running:
            return

        # Try inotify first, fall back to polling
        if not use_polling and self.watch_with_inotify():
            logger.info("inotify watching completed")
        else:
            self.watch_with_polling(poll_interval)

        logger.info("User file watcher stopped")


def main():
    """Main function."""
    if len(sys.argv) < 3:
        print("Usage: watch_user_changes.py <users_json_file> <regenerate_script>")
        print("Example: watch_user_changes.py /secrets/unified_users.json /usr/local/actions/regenerate_http_configs.py")
        sys.exit(1)

    users_file = sys.argv[1]
    regenerate_script = sys.argv[2]

    # Optional arguments
    use_polling = '--polling' in sys.argv
    poll_interval = 5

    # Get poll interval if specified
    if '--interval' in sys.argv:
        try:
            idx = sys.argv.index('--interval')
            poll_interval = int(sys.argv[idx + 1])
        except (IndexError, ValueError):
            logger.warning("Invalid --interval value, using default 5 seconds")

    # Validate regenerate script exists
    if not os.path.exists(regenerate_script):
        logger.error(f"Regeneration script not found: {regenerate_script}")
        sys.exit(1)

    # Make sure regenerate script is executable
    if not os.access(regenerate_script, os.X_OK):
        logger.error(f"Regeneration script is not executable: {regenerate_script}")
        sys.exit(1)

    # Start watching
    watcher = UserFileWatcher(users_file, regenerate_script)
    watcher.start_watching(use_polling=use_polling, poll_interval=poll_interval)


if __name__ == '__main__':
    main()
