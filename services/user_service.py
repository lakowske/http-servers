"""
Provides user services, like finding users and creating users.
"""

from services.config_service import ConfigService
from configuration.tree_nodes import Passwd
from auth.auth import UserCredential


class UserService:
    """
    A service for managing users.
    """

    def __init__(self, config_service: ConfigService):
        self.config_service = config_service
        self.build_paths = config_service.config.build_paths
        self.build_root = config_service.config.build.build_root
        self.passwd: Passwd = self.build_paths.get("secrets").get("passwd")

    def find_user(self, username: str) -> UserCredential:
        """
        Find a user by username.
        """
        users = self.passwd.read(self.build_root)
        for user in users:
            if user.username == username:
                return user
        return None
