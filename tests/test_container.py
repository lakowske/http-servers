"""
This module contains the tests for the container module.
"""

import unittest
import podman
from dependency_injector.wiring import inject, Provide
from configuration.container import ServerContainer
from services.config_service import ConfigService
from services.podman_service import PodmanService


@inject
def create_podman_client(
    podman_service: PodmanService = Provide[ServerContainer.podman_service],
) -> podman.PodmanClient:
    """A simple injection function to create a Podman client."""
    return podman_service.get_client()


class TestContainer(unittest.TestCase):
    """
    Test case for the container module.
    """

    def setUp(self) -> None:
        self.container = ServerContainer()
        # Initialize the container with the test config
        config_service: ConfigService = self.container.config_service()
        config_service.load_yaml_config("tests/test-config.yaml")
        # Wire the container
        self.container.wire(modules=[__name__])

    def test_config(self):
        """
        Test that the container can load custom test-config.yaml configuration
        """
        full_config = self.container.config_service()
        self.assertIsNotNone(full_config)
        self.assertEqual(full_config.config.imap.server, "imap.example.com")

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

    def test_config_service(self):
        """
        Test that the container can create a ConfigService instance.
        """
        # Act
        config_service = self.container.config_service()

        # Assert
        self.assertIsNotNone(config_service)
        self.assertIsNotNone(config_service.config)
        # Load the test config and verify that the values were merged/overwritten
        updates = config_service.load_yaml_config("tests/test-config.yaml")
        self.assertIsNotNone(updates)
        server = updates["imap"]["server"]
        user = updates["imap"]["username"]
        password = updates["imap"]["password"]
        port = updates["imap"]["port"]
        self.assertEqual(config_service.config.imap.server, server)
        self.assertEqual(config_service.config.imap.port, port)
        self.assertEqual(config_service.config.imap.username, user)
        self.assertEqual(config_service.config.imap.password, password)

    def test_wiring(self):
        """
        Verify that wiring worked.
        """
        # Act
        podman_client = create_podman_client()

        # Assert
        self.assertIsNotNone(podman_client)
        self.assertIsInstance(podman_client, podman.PodmanClient)
