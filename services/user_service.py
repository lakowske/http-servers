"""
Provides user services, like finding users and creating users.
"""

from typing import List
from services.config_service import ConfigService
from configuration.tree_nodes import Htpasswd, Passwd, git_auth, passwd
from auth.auth import UserCredential
from auth.password import random_password


class UserService:
    """
    A service for managing users.
    """

    def __init__(self, config_service: ConfigService, sync_on_write: bool = True):
        self.config_service = config_service
        self.build_paths = config_service.config.build_paths
        self.build_root = config_service.config.build.build_root
        self.passwd: Passwd = passwd
        self.htpasswd: Htpasswd = git_auth
        self.htpasswd_path = self.htpasswd.tree_root_path(self.build_root)
        self.passwd_path = self.passwd.tree_root_path(self.build_root)
        self.users: List[UserCredential] = []
        self.ht = None
        self.sync_on_write = sync_on_write

        self.create_or_read()

    def write(self):
        """
        Write the user state to the filesystem.
        """
        self.passwd.render(self.build_root, self.users, overwrite=True)
        self.htpasswd.render(self.build_root, self.users, overwrite=True)

    def read(self):
        """
        Read the users from the filesystem.
        """
        self.users = self.passwd.read(self.build_root)
        self.ht = self.htpasswd.read(self.build_root)

    def reset(self):
        """
        Reset the users.
        """
        self.users = []
        self.ht = None
        self.create()
        self.read()

    def create(self):
        """
        Create the users in the filesystem.
        """
        self.passwd.render(self.build_root, self.users, overwrite=True)
        self.htpasswd.render(self.build_root, self.users, overwrite=True)

    def create_or_read(self):
        """
        Create or read the users from the filesystem.
        """
        if not self.passwd.exists(self.build_root) or not self.htpasswd.exists(
            self.build_root
        ):
            self.create()

        self.read()

    def find_user(self, username: str) -> UserCredential:
        """
        Find a user by username.
        """
        for user in self.users:
            if user.username == username:
                return user
        return None

    def create_user(self, username: str, password: str):
        """
        Create a user.
        """
        user = UserCredential(username=username, password=password)
        self.users.append(user)
        self.ht.set_password(username, password)
        if self.sync_on_write:
            self.write()

    def delete_user(self, username: str):
        """
        Remove a user.
        """
        for i, u in enumerate(self.users):
            if u.username == username:
                self.users.pop(i)
        self.ht.delete(username)
        if self.sync_on_write:
            self.write()

    def update_user(self, user: UserCredential):
        """
        Update a user.
        """
        for i, u in enumerate(self.users):
            if u.username == user.username:
                self.users[i] = user
        self.ht.set_password(user.username, user.password)
        if self.sync_on_write:
            self.write()

    def random_password(self, username: str):
        """
        Generate a random password for a user.
        """
        user = self.find_user(username)
        if user is None:
            raise ValueError(f"User {username} not found.")
        user.password = random_password(20)
        self.update_user(user)
        return user.password
