import unittest
import subprocess
import os

class TestCLI(unittest.TestCase):

    def test_templates(self):
        result = subprocess.run(['python', 'http-servers/cli.py', 'templates', '--domain', 'example.com'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(os.path.exists('apache/conf/extra/httpd-ssl.conf'))
        self.assertTrue(os.path.exists('apache/Dockerfile'))
        self.assertTrue(os.path.exists('certbot/Dockerfile'))

    def test_images(self):
        result = subprocess.run(['python', 'http-servers/cli.py', 'images'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)

    def test_run(self):
        result = subprocess.run(['python', 'http-servers/cli.py', 'run', '--domain', 'example.com', '--email', 'test@example.com'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)

    def test_rm(self):
        result = subprocess.run(['python', 'http-servers/cli.py', 'rm'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)

if __name__ == '__main__':
    unittest.main()