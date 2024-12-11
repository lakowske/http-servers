"""
Integration tests for the podman service.
"""

from configuration.container import ServerContainer
from actions.build import (
    build_image,
    build,
    list_containers,
    run_container,
    health,
    reload_httpd,
    rm_container,
    rm_image,
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


def test_build_and_render_with_secrets_config():
    """
    Test that the config service can render the configuration with secrets.
    """
    build()


def test_httpd_service_run_container():
    """
    Test that the httpd service can run a container.
    """
    run_container()


def test_httpd_service_reload_configuration():
    """
    Test that the httpd service can reload the configuration of a container.
    """
    reload_httpd()


def test_httpd_service_reload_configuration():
    """
    Test that the httpd service can reload the configuration of a container.
    """
    container_id = httpd_service.get_container_id("httpd-nexus")
    assert container_id is not None
    httpd_service.reload_configuration(container_id)
    assert httpd_service.is_container_running(container_id)


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
