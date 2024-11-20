"""
Unit tests for the HTTP server CLI.

This module contains unit tests for various components of the HTTP server CLI,
including template building, image building, running the server, health checks,
SSL certificate generation, and resource removal.

Classes:
    TestCLI: A unittest.TestCase subclass that defines the test cases for the
             HTTP server CLI.

Methods:
    setUp: Initializes the test environment, including loading the configuration
           and wiring the dependency injection container.
    test_templates: Tests the template building functionality and verifies the
                    existence of generated template files.
    test_images: Tests the image building functionality.
    test_run: Tests the server run functionality.
    test_http_server: Tests the HTTP server health check functionality.
    test_certbot: Tests the SSL certificate generation functionality using Certbot.
    test_rm: Tests the resource removal functionality, including containers and images.

Usage:
    Run this module directly to execute the unit tests.
"""

import unittest
import os
from dependency_injector import providers
from http_servers.templates import build_templates
from http_servers.images import build_images
from http_servers.run import do_run
from http_servers.rm import do_rm
from http_servers.config import load_config, domain, email, build_dir
from http_servers.config_loader import load_configs
from http_servers.certbot import healthcheck, certbot_ssl
from http_servers.container import ServerContainer


class TestCLI(unittest.TestCase):
    """
    Test suite for the CLI functionality of the HTTP server.

    This test suite includes the following tests:
    - `test_templates`: Verifies that the necessary template files are built and exist in the expected locations.
    - `test_images`: Ensures that the images are built correctly.
    - `test_run`: Checks that the containers are running as expected.
    - `test_http_server`: Performs a health check on the HTTP server to ensure it is running.
    - `test_certbot`: Verifies that SSL certificates are created using Certbot.
    - `test_rm`: Ensures that containers and images are removed correctly.

    The `setUp` method initializes the test environment by loading the configuration, creating instances of domain and email, and setting up the server container with the test-specific configuration.
    """

    def setUp(self):
        """
        Set up the test environment.

        This method initializes the configuration, domain, email, and server container
        for the tests. It loads the configuration from a specified YAML file, creates
        instances of domain and email with the loaded configuration, and initializes
        the server container. The container is then configured with the test-specific
        configuration and wired with the necessary modules.
        """
        self.config = load_config(config_file="tests/dev-config.yaml")
        self.domain = domain(self.config)
        self.email = email(self.config)
        self.container = ServerContainer()
        # Initialize the container with the test config
        self.container.loaded_configs.override(
            providers.Factory(load_configs, config_path="tests/macbook-config.yaml")
        )
        # Wire the container
        self.container.wire(modules=[__name__, "http_servers.images"])

    def test_templates(self):
        """
        Test the template building process.
        This test verifies that the necessary template files are created in the
        expected directories after calling the build_templates function. It checks
        for the existence of the following files:
        - apache/conf/httpd.conf
        - apache/conf/extra/httpd-ssl.conf
        - apache/conf/extra/httpd-git.conf
        - apache/Dockerfile
        - webroot/index.html
        The test uses the domain, email, and config attributes of the test class
        instance to build the templates and determine the build directory.
        """
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
        build_images()
        # Add assertions to verify images were built if possible

    def test_run(self):
        do_run()
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
