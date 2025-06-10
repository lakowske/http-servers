"""
Tests for event handlers.
"""

import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

# Add the project root to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from events.models import ChangeType, Event, EventStatus, EventType
from events.subscriber import ConfigChangeHandler, TemplateChangeHandler, UserChangeHandler


@pytest.mark.events
@pytest.mark.events_unit
class TestEventHandlers:
    """Test event handler functionality."""

    def test_config_change_handler(self):
        """Test configuration change handler."""
        # Mock config service
        mock_config_service = Mock()
        mock_render_callback = Mock()

        handler = ConfigChangeHandler(mock_config_service, mock_render_callback)

        # Create config change event
        event = Event(
            event_type=EventType.CONFIG_CHANGED, source_path="/test/config.yaml", change_type=ChangeType.MODIFIED
        )

        # Test handler can handle event
        assert handler.can_handle(event)

        # Handle event
        result = handler.handle(event)

        # Verify callbacks were called
        mock_config_service.load_yaml_config.assert_called_once_with("/test/config.yaml")
        mock_render_callback.assert_called_once()

        # Verify result
        assert result.event_id == event.id
        assert result.status == EventStatus.COMPLETED

    def test_config_handler_validation_failure(self):
        """Test config handler with validation failure."""
        mock_config_service = Mock()
        mock_config_service.load_yaml_config.side_effect = Exception("Invalid YAML")

        handler = ConfigChangeHandler(mock_config_service, None)

        event = Event(
            event_type=EventType.CONFIG_CHANGED, source_path="/test/config.yaml", change_type=ChangeType.MODIFIED
        )

        result = handler.handle(event)

        assert result.status == EventStatus.FAILED
        assert "Configuration validation failed" in result.error

    def test_template_change_handler(self):
        """Test template change handler."""
        mock_render_callback = Mock()
        mock_reload_callback = Mock()

        handler = TemplateChangeHandler(mock_render_callback, mock_reload_callback)

        # Create template change event
        event = Event(
            event_type=EventType.TEMPLATE_CHANGED, source_path="/templates/httpd.conf", change_type=ChangeType.MODIFIED
        )

        # Test handler can handle event
        assert handler.can_handle(event)

        # Handle event
        result = handler.handle(event)

        # Verify callbacks were called
        mock_render_callback.assert_called_once()
        mock_reload_callback.assert_called_once()

        # Verify affected services determination
        affected_services = handler._determine_affected_services("/templates/httpd.conf")
        assert "httpd" in affected_services

    def test_template_handler_service_detection(self):
        """Test template handler service detection logic."""
        handler = TemplateChangeHandler()

        # Test HTTP service detection
        httpd_templates = ["/templates/httpd.conf", "/templates/apache/ssl.conf", "/templates/git/gitweb.conf"]

        for template_path in httpd_templates:
            services = handler._determine_affected_services(template_path)
            assert "httpd" in services

        # Test mail service detection
        mail_templates = ["/templates/postfix.cf", "/templates/dovecot.conf", "/templates/mail/supervisor.conf"]

        for template_path in mail_templates:
            services = handler._determine_affected_services(template_path)
            assert "mail" in services

        # Test unknown template (should affect both)
        services = handler._determine_affected_services("/templates/unknown.conf")
        assert "httpd" in services
        assert "mail" in services

    def test_user_change_handler(self):
        """Test user change handler."""
        mock_regenerate_callback = Mock()

        handler = UserChangeHandler(mock_regenerate_callback)

        # Create user change event
        event = Event(
            event_type=EventType.USER_CHANGED,
            source_path="/secrets/unified_users.json",
            change_type=ChangeType.MODIFIED,
        )

        # Test handler can handle event
        assert handler.can_handle(event)

        # Handle event
        result = handler.handle(event)

        # Verify callback was called
        mock_regenerate_callback.assert_called_once_with("/secrets/unified_users.json")

        # Verify result
        assert result.event_id == event.id
        assert result.status == EventStatus.COMPLETED

    def test_handler_type_filtering(self):
        """Test that handlers only accept their designated event types."""
        config_handler = ConfigChangeHandler()
        template_handler = TemplateChangeHandler()
        user_handler = UserChangeHandler()

        config_event = Event(
            event_type=EventType.CONFIG_CHANGED, source_path="/test/config.yaml", change_type=ChangeType.MODIFIED
        )

        template_event = Event(
            event_type=EventType.TEMPLATE_CHANGED, source_path="/test/template.conf", change_type=ChangeType.MODIFIED
        )

        user_event = Event(
            event_type=EventType.USER_CHANGED, source_path="/test/users.json", change_type=ChangeType.MODIFIED
        )

        # Config handler
        assert config_handler.can_handle(config_event)
        assert not config_handler.can_handle(template_event)
        assert not config_handler.can_handle(user_event)

        # Template handler
        assert not template_handler.can_handle(config_event)
        assert template_handler.can_handle(template_event)
        assert not template_handler.can_handle(user_event)

        # User handler
        assert not user_handler.can_handle(config_event)
        assert not user_handler.can_handle(template_event)
        assert user_handler.can_handle(user_event)

    def test_handler_error_handling(self):
        """Test handler error handling."""
        # Test config handler with render failure
        mock_render_callback = Mock()
        mock_render_callback.side_effect = Exception("Render failed")

        handler = ConfigChangeHandler(None, mock_render_callback)

        event = Event(
            event_type=EventType.CONFIG_CHANGED, source_path="/test/config.yaml", change_type=ChangeType.MODIFIED
        )

        result = handler.handle(event)

        assert result.status == EventStatus.FAILED
        assert "Template rendering failed" in result.error

    def test_handler_without_callbacks(self):
        """Test handlers work without callbacks (no-op behavior)."""
        # Handlers should work even without callbacks
        config_handler = ConfigChangeHandler()
        template_handler = TemplateChangeHandler()
        user_handler = UserChangeHandler()

        events = [
            Event(
                event_type=EventType.CONFIG_CHANGED, source_path="/test/config.yaml", change_type=ChangeType.MODIFIED
            ),
            Event(
                event_type=EventType.TEMPLATE_CHANGED,
                source_path="/test/template.conf",
                change_type=ChangeType.MODIFIED,
            ),
            Event(event_type=EventType.USER_CHANGED, source_path="/test/users.json", change_type=ChangeType.MODIFIED),
        ]

        handlers = [config_handler, template_handler, user_handler]

        # All should complete successfully even without callbacks
        for handler, event in zip(handlers, events):
            if handler.can_handle(event):
                result = handler.handle(event)
                assert result.status == EventStatus.COMPLETED
