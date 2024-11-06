import unittest
import os
from click.testing import CliRunner
from http_servers.templates import templates, build_templates
from http_servers.images import images, build_images
from http_servers.run import run, do_run
from http_servers.rm import rm, do_rm
from http_servers.config import load_config
from http_servers.ssl import healthcheck

class TestCLI(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()
        self.config = load_config()
        self.domain = 'lab.sethlakowske.com'
        self.email  = 'admin@' + self.domain

    def test_templates(self):
        build_templates(self.domain, self.email)
        build_dir = os.path.join(os.path.dirname(__file__), '..', self.config['build_dir'])
        self.assertTrue(os.path.exists(os.path.join(build_dir, 'apache/conf/httpd.conf')))
        self.assertTrue(os.path.exists(os.path.join(build_dir, 'apache/conf/extra/httpd-ssl.conf')))
        self.assertTrue(os.path.exists(os.path.join(build_dir, 'apache/Dockerfile')))
        self.assertTrue(os.path.exists(os.path.join(build_dir, 'webroot/index.html')))

    def test_images(self):
        build_images()
        # Add assertions to verify images were built if possible

    def test_run(self):
        result = do_run(self.domain, self.email)
        #result = self.runner.invoke(run, ['--domain', 'example.com', '--email', 'test@example.com'])
        #self.assertEqual(result.exit_code, 0)
        # Add assertions to verify containers are running if possible

    def test_http_server(self):
        result = healthcheck()
        self.assertTrue(result)
        # Add assertions to verify http server is running if possible

    def test_rm(self):
        result = do_rm()
        # Add assertions to verify containers and images were removed if possible

if __name__ == '__main__':
    unittest.main()