#!/usr/bin/env python3
"""
Demo script for the file-based event system.

This script demonstrates the event system working on the host system
without requiring containers.
"""

import argparse
import json
import logging
import tempfile
import time
from pathlib import Path

from events.models import EventType
from events.publisher import EventPublisher, FileWatcherConfig
from events.queue import EventQueue
from events.subscriber import create_config_subscriber

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def demo_basic_functionality():
    """Demonstrate basic event system functionality."""
    logger.info("=== Basic Event System Demo ===")

    with tempfile.TemporaryDirectory(prefix="events_demo_") as temp_dir:
        temp_path = Path(temp_dir)

        # Set up directories
        events_dir = temp_path / "events"
        config_dir = temp_path / "config"
        config_dir.mkdir()

        # Create event queue
        event_queue = EventQueue(str(events_dir))

        # Create test config file
        config_file = config_dir / "test.yaml"
        config_file.write_text(
            """
admin:
  domain: demo.example.com
  email: admin@demo.example.com
"""
        )

        logger.info(f"Created test config: {config_file}")

        # Set up publisher to watch config file
        watch_config = FileWatcherConfig(path=str(config_file), event_type=EventType.CONFIG_CHANGED)
        publisher = EventPublisher(event_queue, [watch_config])

        # Initial scan
        logger.info("Performing initial scan...")
        events = publisher._scan_for_changes(watch_config)
        for event in events:
            event_queue.publish(event)

        logger.info(f"Published {len(events)} initial events")

        # Modify config file
        logger.info("Modifying config file...")
        time.sleep(0.1)  # Ensure timestamp changes
        config_file.write_text(
            """
admin:
  domain: modified.example.com
  email: admin@modified.example.com
  debug: true
"""
        )

        # Scan for changes
        events = publisher._scan_for_changes(watch_config)
        for event in events:
            event_queue.publish(event)

        logger.info(f"Published {len(events)} change events")

        # Create subscriber with mock callbacks
        def mock_config_validation(config_path):
            logger.info(f"Mock: Validating config at {config_path}")

        def mock_render():
            logger.info("Mock: Rendering templates")

        class MockConfigService:
            def load_yaml_config(self, path):
                mock_config_validation(path)

        subscriber = create_config_subscriber(
            event_queue, config_service=MockConfigService(), render_callback=mock_render
        )

        # Process events
        logger.info("Processing events...")
        processed = subscriber.process_events(max_events=10)
        logger.info(f"Processed {processed} events")

        # Show queue stats
        stats = event_queue.get_queue_stats()
        logger.info(f"Queue stats: {stats}")


def demo_multiple_file_types():
    """Demonstrate handling multiple file types."""
    logger.info("=== Multiple File Types Demo ===")

    with tempfile.TemporaryDirectory(prefix="events_multi_") as temp_dir:
        temp_path = Path(temp_dir)

        # Set up directories
        events_dir = temp_path / "events"
        config_dir = temp_path / "config"
        templates_dir = temp_path / "templates"
        config_dir.mkdir()
        templates_dir.mkdir()

        # Create event queue
        event_queue = EventQueue(str(events_dir))

        # Create multiple file types
        config_file = config_dir / "config.yaml"
        config_file.write_text("admin:\n  domain: test.com")

        template_file = templates_dir / "httpd.conf"
        template_file.write_text("# Apache config template")

        user_file = config_dir / "users.json"
        user_file.write_text(json.dumps({"users": [{"name": "testuser"}]}))

        # Set up publisher for all file types
        watch_configs = [
            FileWatcherConfig(str(config_file), EventType.CONFIG_CHANGED),
            FileWatcherConfig(str(template_file), EventType.TEMPLATE_CHANGED),
            FileWatcherConfig(str(user_file), EventType.USER_CHANGED),
        ]

        publisher = EventPublisher(event_queue, watch_configs)

        # Initial scan
        all_events = []
        for config in watch_configs:
            events = publisher._scan_for_changes(config)
            all_events.extend(events)
            for event in events:
                event_queue.publish(event)

        logger.info(f"Published {len(all_events)} initial events")

        # Modify all files
        time.sleep(0.1)
        config_file.write_text("admin:\n  domain: modified.com")
        template_file.write_text("# Modified Apache config")
        user_file.write_text(json.dumps({"users": [{"name": "newuser"}]}))

        # Scan for all changes
        all_events = []
        for config in watch_configs:
            events = publisher._scan_for_changes(config)
            all_events.extend(events)
            for event in events:
                event_queue.publish(event)

        logger.info(f"Published {len(all_events)} change events")

        # Create comprehensive subscriber
        subscriber = create_config_subscriber(
            event_queue,
            config_service=None,  # Skip validation for demo
            render_callback=lambda: logger.info("Mock: Rendering all templates"),
            reload_callback=lambda services: logger.info(f"Mock: Reloading {services}"),
            regenerate_callback=lambda path: logger.info(f"Mock: Regenerating auth from {path}"),
        )

        # Process all events
        processed = subscriber.process_events(max_events=20)
        logger.info(f"Processed {processed} events")

        # Show final stats
        stats = event_queue.get_queue_stats()
        logger.info(f"Final queue stats: {stats}")


def demo_directory_watching():
    """Demonstrate recursive directory watching."""
    logger.info("=== Directory Watching Demo ===")

    with tempfile.TemporaryDirectory(prefix="events_dir_") as temp_dir:
        temp_path = Path(temp_dir)

        # Set up directories
        events_dir = temp_path / "events"
        templates_dir = temp_path / "templates"
        templates_dir.mkdir()

        # Create subdirectories
        (templates_dir / "httpd").mkdir()
        (templates_dir / "mail").mkdir()

        # Create event queue
        event_queue = EventQueue(str(events_dir))

        # Set up recursive directory watching
        watch_config = FileWatcherConfig(path=str(templates_dir), event_type=EventType.TEMPLATE_CHANGED, recursive=True)
        publisher = EventPublisher(event_queue, [watch_config])

        # Create files in various subdirectories
        files_to_create = [
            templates_dir / "main.conf",
            templates_dir / "httpd" / "ssl.conf",
            templates_dir / "httpd" / "vhosts.conf",
            templates_dir / "mail" / "postfix.cf",
            templates_dir / "mail" / "dovecot.conf",
        ]

        for file_path in files_to_create:
            file_path.write_text(f"# Template: {file_path.name}")
            logger.info(f"Created: {file_path}")

        # Scan for all files
        events = publisher._scan_for_changes(watch_config)
        for event in events:
            event_queue.publish(event)

        logger.info(f"Detected {len(events)} files in directory tree")

        # Modify some files
        time.sleep(0.1)
        (templates_dir / "main.conf").write_text("# Modified main config")
        (templates_dir / "httpd" / "ssl.conf").write_text("# Modified SSL config")

        # Scan for changes
        events = publisher._scan_for_changes(watch_config)
        for event in events:
            event_queue.publish(event)

        logger.info(f"Detected {len(events)} file changes")

        # Process events
        subscriber = create_config_subscriber(
            event_queue, render_callback=lambda: logger.info("Mock: Re-rendering templates")
        )

        processed = subscriber.process_events(max_events=20)
        logger.info(f"Processed {processed} events")


def main():
    """Main demo function."""
    parser = argparse.ArgumentParser(description="Event System Demo")
    parser.add_argument(
        "--demo", choices=["basic", "multi", "directory", "all"], default="all", help="Which demo to run"
    )

    args = parser.parse_args()

    logger.info("Starting Event System Demo")
    logger.info("This demo shows the event system working entirely on the host")
    logger.info("without requiring containers or external dependencies.")
    logger.info("")

    if args.demo in ["basic", "all"]:
        demo_basic_functionality()
        logger.info("")

    if args.demo in ["multi", "all"]:
        demo_multiple_file_types()
        logger.info("")

    if args.demo in ["directory", "all"]:
        demo_directory_watching()
        logger.info("")

    logger.info("Demo completed successfully!")
    logger.info("")
    logger.info("Key takeaways:")
    logger.info("- File changes are detected automatically")
    logger.info("- Events are queued reliably using filesystem")
    logger.info("- Subscribers process events independently")
    logger.info("- System works without external dependencies")
    logger.info("- Perfect for container communication via shared volumes")


if __name__ == "__main__":
    main()
