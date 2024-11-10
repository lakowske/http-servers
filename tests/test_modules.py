import unittest
import os
from click.testing import CliRunner
from http_servers.templates import templates, build_templates
from http_servers.images import images, build_images
from http_servers.run import run, do_run
from http_servers.rm import rm, do_rm
from http_servers.config import load_config, domain, email, build_dir
from http_servers.ssl import healthcheck, certbot_ssl


class TestCLI(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()
        self.config = load_config(config_file='tests/dev-config.yaml')
        self.domain = domain(self.config)
        self.email  = email(self.config)

    def test_templates(self):
        build_templates(self.domain, self.email, self.config)
        template_build_dir = build_dir(self.config)
        self.assertTrue(os.path.exists(os.path.join(template_build_dir, 'apache/conf/httpd.conf')))
        self.assertTrue(os.path.exists(os.path.join(template_build_dir, 'apache/conf/extra/httpd-ssl.conf')))
        self.assertTrue(os.path.exists(os.path.join(template_build_dir, 'apache/Dockerfile')))
        self.assertTrue(os.path.exists(os.path.join(template_build_dir, 'webroot/index.html')))

    def test_images(self):
        build_images()
        # Add assertions to verify images were built if possible

    def test_run(self):
        result = do_run(self.domain, self.email)
        #result = self.runner.invoke(run, ['--domain', 'example.com', '--email', 'test@example.com'])
        #self.assertEqual(result.exit_code, 0)
        # Add assertions to verify containers are running if possible

    def test_http_server(self):
        result = healthcheck(self.domain)
        self.assertTrue(result)
        # Add assertions to verify http server is running if possible

    def test_certbot(self):
        result = certbot_ssl([self.domain], self.email, config=self.config, dry_run=False)
        self.assertTrue(result)
        # Add assertions to verify certificates were created if possible

    def test_rm(self):
        result = do_rm()
        # Add assertions to verify containers and images were removed if possible

if __name__ == '__main__':
    unittest.main()