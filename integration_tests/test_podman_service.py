"""
Integration tests for the podman service.
"""

from configuration.container import ServerContainer
from actions.build import (
    build_image,
    build,
    render,
    list_containers,
    run_container,
    health,
    reload_httpd,
    rm_container,
    rm_image,
    create_git_repo_volume,
    remove_git_repo_volume,
    create_test_repo,
)


container = ServerContainer()
podman_service = container.podman_service()
config_service = container.config_service()
config_service.load_yaml_config("secrets/config.yaml")
httpd_service = container.httpd_service()


def test_podman_list_containers():
    """
    Test that the podman service can list containers.
    """
    containers = list_containers()
    assert containers is not None


def test_build():
    """
    Test that the podman service can build an image.
    """
    build_image()


def test_render():
    """
    Test rendering the configuration tree into a build directory.
    """
    render()


def test_build_and_render_with_secrets_config():
    """
    Test that the config service can render the configuration with secrets.
    """
    build()


def test_git_repo_volume_creation():
    """
    Test that the podman service can create a git repo.
    """
    create_git_repo_volume()


def test_git_repo_volume_removal():
    """
    Test that the podman service can remove a git repo.
    """
    remove_git_repo_volume()


def test_create_test_repo():
    """
    Test that the podman service can create a test repo.
    """
    create_test_repo()


def test_httpd_service_run_container():
    """
    Test that the httpd service can run a container.
    """
    run_container()


def test_reload():
    """
    Test that the httpd service can reload the configuration of a container.
    """
    reload_httpd()


def test_http_healthcheck():
    """
    Test that the podman service can perform an http healthcheck on a container.
    """
    health()


def test_podman_rm_container():
    """
    Test that the podman service can remove a container.
    """
    rm_container()


def test_podman_rm_image():
    """
    Test that the podman service can remove an image.
    """
    rm_image()
