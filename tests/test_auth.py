import unittest
from http_servers.auth import UserCredential, to_htpasswd_file, from_htpasswd_file, from_htpasswd_str, to_htpasswd_str
from passlib.apache import HtpasswdFile
import os

class TestAuth(unittest.TestCase):

    def setUp(self):
        self.users = [
            UserCredential(username="user1", password="password1"),
            UserCredential(username="user2", password="password2")
        ]
        self.file_path = "/tmp/test_htpasswd"
        self.htpasswd_str = "user1:$apr1$H6uskkkW$IgXLP6ewTrSuBkTrqE8wj/\nuser2:$apr1$H6uskkkW$IgXLP6ewTrSuBkTrqE8wj/\n"

    def tearDown(self):
        if os.path.exists(self.file_path):
            os.remove(self.file_path)

    def test_to_htpasswd_file(self):
        to_htpasswd_file(self.users, self.file_path)
        ht = HtpasswdFile(self.file_path)
        self.assertTrue(ht.check_password("user1", "password1"))
        self.assertTrue(ht.check_password("user2", "password2"))

    def test_from_htpasswd_file(self):
        to_htpasswd_file(self.users, self.file_path)
        ht = from_htpasswd_file(self.file_path)
        self.assertTrue(ht.check_password("user1", "password1"))
        self.assertTrue(ht.check_password("user2", "password2"))

    def test_to_from_htpasswd_str(self):
        user = UserCredential(username="user1", password="password1")
        htpasswd_entry = to_htpasswd_str(user)
        ht = from_htpasswd_str(htpasswd_entry)
        self.assertTrue(ht.check_password("user1", "password1"))

if __name__ == '__main__':
    unittest.main()
