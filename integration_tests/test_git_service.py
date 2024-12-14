"""
This module contains tests for the git_service module.
"""

from configuration.container import ServerContainer
from services.config_service import ConfigService


container = ServerContainer()
config_service: ConfigService = container.config_service()
config_service.load_yaml_config("secrets/config.yaml")

TEST_REPO_NAME = "test_repo"


def test_create_bare_repo():
    """
    Test the create_bare_repo function to ensure it creates a bare repository.
    """
    git_service = container.git_service()
    repo = git_service.create_bare_repo(TEST_REPO_NAME)
    assert repo.bare is True


def test_clone_repo():
    """
    Test the ability to clone our test repository from the https server.
    """
    git_service = container.git_service()
    user_service = container.user_service()
    git_user = user_service.find_user("git")
    assert git_user is not None
    repo_url = f"https://{git_user.username}:{git_user.password}@{config_service.config.admin.domain}/git/{TEST_REPO_NAME}"
    clone_repo_path = "./test_repo"
    git_service.clone_repo(clone_repo_path, repo_url)
