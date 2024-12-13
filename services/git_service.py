"""
Git service provides a service for interacting with a set of local git repositories.
"""

import os
from git import Repo
from services.config_service import ConfigService
from configuration.app import WORKSPACE


class GitService:
    """
    A service class to interact with a set of local git repositories.
    """

    def __init__(self, config_service: ConfigService):
        self.config_service = config_service
        self.build_paths = config_service.config.build_paths
        self.git_repos_path = (
            self.build_paths.get("apache").get("git").tree_root_path(WORKSPACE)
        )

    def create_bare_repo(self, repo_name):
        """
        Create a bare repository
        """
        repo_path = os.path.join(self.git_repos_path, repo_name)
        return Repo.init(repo_path, bare=True)

    def clone_repo(self, clone_repo_path, repo_url):
        """
        Clone a repository
        """
        return Repo.clone_from(repo_url, clone_repo_path)
