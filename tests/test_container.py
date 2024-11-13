import unittest
from http_servers.container import ServerContainer
from http_servers.service import PodmanService
from http_servers.config_loader import load_configs
from dependency_injector import providers
from dependency_injector.wiring import inject, Provide

@inject
def create_podman_client(podman_service: PodmanService = Provide[ServerContainer.podman_service]):
    return podman_service.get_client()

class TestContainer(unittest.TestCase):
    def setUp(self) -> None:
        self.container = ServerContainer()
        # Initialize the container with the test config
        self.container.loaded_configs.override(
            providers.Factory(
                load_configs,
                config_path="tests/test-config.yaml"
            )
        )
        # Wire the container
        self.container.wire(modules=[__name__])

    def test_config(self):
        full_config = self.container.loaded_configs()
        self.assertIsInstance(full_config, dict)
        self.assertIn("podman", full_config)
        self.assertEqual(28, full_config["test_value"])

    def test_podman_service(self):
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

    def test_wiring(self):
        # Act
        podman_client = create_podman_client()

        # Assert
        self.assertIsNotNone(podman_client)
