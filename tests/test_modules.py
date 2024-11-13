import unittest
import os
from http_servers.templates import build_templates
from http_servers.images import build_images
from http_servers.run import do_run
from http_servers.rm import do_rm
from http_servers.config import load_config, domain, email, build_dir
from http_servers.config_loader import load_configs
from http_servers.certbot import healthcheck, certbot_ssl
from http_servers.container import ServerContainer
from dependency_injector import providers


class TestCLI(unittest.TestCase):

    def setUp(self):
        self.config = load_config(config_file="tests/dev-config.yaml")
        self.domain = domain(self.config)
        self.email = email(self.config)
        self.container = ServerContainer()
        # Initialize the container with the test config
        self.container.loaded_configs.override(
            providers.Factory(
                load_configs,
                config_path="tests/macbook-config.yaml"
            )
        )
        # Wire the container
        self.container.wire(modules=[__name__, 'http_servers.images'])

    def test_templates(self):
        build_templates(self.domain, self.email, self.config)
        template_build_dir = build_dir(self.config)
        self.assertTrue(
            os.path.exists(os.path.join(template_build_dir, "apache/conf/httpd.conf"))
        )
        self.assertTrue(
            os.path.exists(
                os.path.join(template_build_dir, "apache/conf/extra/httpd-ssl.conf")
            )
        )
        self.assertTrue(
            os.path.exists(
                os.path.join(template_build_dir, "apache/conf/extra/httpd-git.conf")
            )
        )
        self.assertTrue(
            os.path.exists(os.path.join(template_build_dir, "apache/Dockerfile"))
        )
        self.assertTrue(
            os.path.exists(os.path.join(template_build_dir, "webroot/index.html"))
        )

    def test_images(self):
        loaded_configs = self.container.loaded_configs()
        podman_configs = self.container.podman_config()
        podman_service = self.container.podman_service()

        build_images()
        # Add assertions to verify images were built if possible

    def test_run(self):
        result = do_run(self.domain, self.email)
        # result = self.runner.invoke(run, ['--domain', 'example.com', '--email', 'test@example.com'])
        # self.assertEqual(result.exit_code, 0)
        # Add assertions to verify containers are running if possible

    def test_http_server(self):
        result = healthcheck(self.domain)
        self.assertTrue(result)
        # Add assertions to verify http server is running if possible

    def test_certbot(self):
        result = certbot_ssl(
            [self.domain], self.email, config=self.config, dry_run=False
        )
        self.assertTrue(result)
        # Add assertions to verify certificates were created if possible

    def test_rm(self):
        result = do_rm()
        # Add assertions to verify containers and images were removed if possible


if __name__ == "__main__":
    unittest.main()
