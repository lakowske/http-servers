"""
Command line interface for the event system.

Provides commands for running publishers and subscribers in isolation
for testing and development.
"""

import argparse
import logging
import signal
import sys
from pathlib import Path

from .models import EventType
from .publisher import EventPublisher, FileWatcherConfig, create_config_publisher
from .queue import EventQueue
from .subscriber import create_config_subscriber

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def setup_signal_handlers(publisher=None, subscriber=None):
    """Set up signal handlers for graceful shutdown.

    Args:
        publisher: Event publisher instance
        subscriber: Event subscriber instance
    """

    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down")
        if publisher:
            publisher.running = False
        if subscriber:
            subscriber.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def cmd_publish(args):
    """Run event publisher command."""
    logger.info(f"Starting event publisher with queue at {args.queue_dir}")

    # Create event queue
    event_queue = EventQueue(args.queue_dir)

    if args.config_mode:
        # Use pre-configured publisher for standard config files
        publisher = create_config_publisher(event_queue, config_dir=args.config_dir, templates_dir=args.templates_dir)
    else:
        # Create custom publisher from command line args
        watch_configs = []
        for watch_path in args.watch_paths:
            # Determine event type from path
            event_type = EventType.CONFIG_CHANGED
            if "template" in watch_path.lower():
                event_type = EventType.TEMPLATE_CHANGED
            elif "user" in watch_path.lower():
                event_type = EventType.USER_CHANGED

            config = FileWatcherConfig(path=watch_path, event_type=event_type, recursive=args.recursive)
            watch_configs.append(config)

        publisher = EventPublisher(event_queue, watch_configs)

    # Set up signal handlers
    setup_signal_handlers(publisher=publisher)

    # Start watching
    try:
        publisher.start_watching(use_polling=args.polling, poll_interval=args.interval)
    except KeyboardInterrupt:
        logger.info("Publisher stopped by user")


def cmd_subscribe(args):
    """Run event subscriber command."""
    logger.info(f"Starting event subscriber with queue at {args.queue_dir}")

    # Create event queue
    event_queue = EventQueue(args.queue_dir)

    # Create mock callbacks for testing
    def mock_config_service():
        class MockConfigService:
            def load_yaml_config(self, config_path):
                logger.info(f"Mock: Loading config from {config_path}")

        return MockConfigService()

    def mock_render_callback():
        logger.info("Mock: Rendering configuration templates")

    def mock_reload_callback(services):
        logger.info(f"Mock: Reloading services: {services}")

    def mock_regenerate_callback(user_file):
        logger.info(f"Mock: Regenerating auth files from {user_file}")

    # Create subscriber
    subscriber = create_config_subscriber(
        event_queue,
        config_service=mock_config_service() if args.enable_validation else None,
        render_callback=mock_render_callback if args.enable_rendering else None,
        reload_callback=mock_reload_callback if args.enable_reloading else None,
        regenerate_callback=mock_regenerate_callback if args.enable_regeneration else None,
    )

    # Set up signal handlers
    setup_signal_handlers(subscriber=subscriber)

    # Start processing
    try:
        subscriber.run(poll_interval=args.interval, max_events_per_batch=args.max_events)
    except KeyboardInterrupt:
        logger.info("Subscriber stopped by user")


def cmd_status(args):
    """Show event queue status."""
    event_queue = EventQueue(args.queue_dir)
    stats = event_queue.get_queue_stats()

    print(f"Event Queue Status ({args.queue_dir}):")
    print(f"  Pending:    {stats.get('pending', 0)}")
    print(f"  Processing: {stats.get('processing', 0)}")
    print(f"  Completed:  {stats.get('completed', 0)}")
    print(f"  Failed:     {stats.get('failed', 0)}")

    if "error" in stats:
        print(f"  Error:      {stats['error']}")


def cmd_cleanup(args):
    """Clean up old events."""
    event_queue = EventQueue(args.queue_dir)

    logger.info(f"Cleaning up events older than {args.max_age} hours")
    event_queue.cleanup_old_events(max_age_hours=args.max_age, max_count=args.max_count)
    logger.info("Cleanup completed")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Event system CLI for configuration change monitoring")
    parser.add_argument(
        "--queue-dir", default="./events_queue", help="Directory for event queue (default: ./events_queue)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Publisher command
    pub_parser = subparsers.add_parser("publish", help="Run event publisher")
    pub_parser.add_argument(
        "--config-mode", action="store_true", help="Use pre-configured publisher for standard config files"
    )
    pub_parser.add_argument("--config-dir", default="secrets", help="Configuration directory (default: secrets)")
    pub_parser.add_argument("--templates-dir", default="templates", help="Templates directory (default: templates)")
    pub_parser.add_argument(
        "--watch-paths", nargs="+", default=[], help="Paths to watch (required if not using --config-mode)"
    )
    pub_parser.add_argument("--recursive", action="store_true", help="Watch directories recursively")
    pub_parser.add_argument("--polling", action="store_true", help="Use polling instead of inotify")
    pub_parser.add_argument("--interval", type=int, default=5, help="Polling interval in seconds (default: 5)")

    # Subscriber command
    sub_parser = subparsers.add_parser("subscribe", help="Run event subscriber")
    sub_parser.add_argument("--enable-validation", action="store_true", help="Enable configuration validation")
    sub_parser.add_argument("--enable-rendering", action="store_true", help="Enable template rendering")
    sub_parser.add_argument("--enable-reloading", action="store_true", help="Enable service reloading")
    sub_parser.add_argument("--enable-regeneration", action="store_true", help="Enable auth file regeneration")
    sub_parser.add_argument("--interval", type=float, default=5.0, help="Poll interval in seconds (default: 5.0)")
    sub_parser.add_argument("--max-events", type=int, default=10, help="Maximum events per batch (default: 10)")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show queue status")

    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up old events")
    cleanup_parser.add_argument("--max-age", type=int, default=24, help="Maximum age in hours (default: 24)")
    cleanup_parser.add_argument("--max-count", type=int, default=1000, help="Maximum events to keep (default: 1000)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Ensure queue directory exists
    Path(args.queue_dir).mkdir(parents=True, exist_ok=True)

    # Route to appropriate command
    if args.command == "publish":
        if not args.config_mode and not args.watch_paths:
            print("Error: Must specify --watch-paths or use --config-mode")
            return
        cmd_publish(args)
    elif args.command == "subscribe":
        cmd_subscribe(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "cleanup":
        cmd_cleanup(args)


if __name__ == "__main__":
    main()
