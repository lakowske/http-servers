"""
This module tests the http git server functionality.
"""

import unittest
from http_servers.auth import UserCredential, from_passwd_file


class TestGit(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_git(self):
        """Clones the test repository and checks if the cloned repository exists."""
        # Read the passwd file for a valid user
        users = from_passwd_file("/tmp/test_passwd")

        cmd = "git clone http://admin:"
        pass
