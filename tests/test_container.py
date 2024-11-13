import unittest
from http_servers.container import Container
from podman.client import PodmanClient

class TestContainer(unittest.TestCase):

    def test_config(self):
        container = Container()
        full_config = container.loaded_configs(config_path="tests/test-config.yaml")
        self.assertIsInstance(full_config, dict)
        self.assertIn("podman", full_config)
        self.assertEqual(28, full_config["test_value"])
