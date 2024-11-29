"""
This module contains the tests for the container module.
"""

import unittest
from dependency_injector import providers
from dependency_injector.wiring import inject, Provide
from configuration.container import ServerContainer
from configuration.config_loader import load_configs
from services.podman_service import PodmanService


@inject
def create_podman_client(
    podman_service: PodmanService = Provide[ServerContainer.podman_service],
):
    """A simple injection function to create a Podman client."""
    return podman_service.get_client()


class TestContainer(unittest.TestCase):
    """
    Test case for the container module.
    """

    def setUp(self) -> None:
        self.container = ServerContainer()
        # Initialize the container with the test config
        self.container.loaded_configs.override(
            providers.Factory(load_configs, config_path="tests/test-config.yaml")
        )
        # Wire the container
        self.container.wire(modules=[__name__])

    def test_config(self):
        """
        Test that the container can load custom test-config.yaml configuration
        """
        full_config = self.container.loaded_configs()
        self.assertIsInstance(full_config, dict)
        self.assertIn("podman", full_config)
        self.assertEqual(28, full_config["test_value"])

    def test_podman_service(self):
        """
        Test that the container can create a PodmanService instance.
        """
        # Act
        podman_config = self.container.podman_config()
        podman_service = self.container.podman_service()

        # Assert
        self.assertIsNotNone(podman_config)
        self.assertEqual(podman_config.socket_url, "unix:///var/run/podman/podman.sock")
        self.assertEqual(podman_config.timeout, 30)
        self.assertTrue(podman_config.tls_verify)

        self.assertIsNotNone(podman_service)
        self.assertEqual(podman_service.podman_config, podman_config)
        self.assertIsNotNone(podman_service.get_client())

    def test_app_config(self):
        """
        Test that the container can create an AppConfig instance.
        """
        # Act
        app_config = self.container.app_config()

        # Assert
        self.assertIsNotNone(app_config)
        self.assertEqual(app_config.admin_context.domain, "example.com")
        self.assertEqual(app_config.admin_context.email, "admin@example.com")

    def test_mail_service(self):
        """
        Test that the container can create a MailService instance.
        """
        # Act
        email_service = self.container.email_service()

        # Assert
        self.assertIsNotNone(email_service)
        self.assertEqual(email_service.imap.server, "localhost")
        self.assertEqual(email_service.imap.port, 1143)
        self.assertIsNone(email_service.imap.username)
        self.assertIsNone(email_service.imap.password)
        self.assertEqual(email_service.smtp.server, "localhost")
        self.assertEqual(email_service.smtp.port, 1025)

    def test_config_service(self):
        """
        Test that the container can create a ConfigService instance.
        """
        # Act
        config_service = self.container.config_service()

        # Assert
        self.assertIsNotNone(config_service)
        self.assertIsNotNone(config_service.config)

    def test_wiring(self):
        """
        Verify that wiring worked.
        """
        # Act
        podman_client = create_podman_client()

        # Assert
        self.assertIsNotNone(podman_client)
