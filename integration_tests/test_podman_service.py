"""
Integration tests for the podman service.
"""

from configuration.tree_walker import TreeRenderer
from configuration.container import ServerContainer
from http_server.health_check import healthcheck
from services.httpd_service import LATEST_IMAGE


container = ServerContainer()
podman_service = container.podman_service()
config_service = container.config_service()
config_service.load_yaml_config("secrets/config.yaml")
httpd_service = container.httpd_service()


def test_podman_list_containers():
    """
    Test that the podman service can list containers.
    """

    containers = podman_service.list_containers()
    assert containers is not None
    assert len(containers) >= 0


def test_render_with_secrets_config():
    """
    Test that the config service can render the configuration with secrets.
    """
    walker = TreeRenderer()
    walker.walk(config_service.config.build_paths, config_service.config)
    assert config_service.config.admin.domain is not None
    assert config_service.config.admin.email is not None
    assert config_service.config.build_paths is not None
    assert config_service.config.container_paths is not None
    assert config_service.config.runtime is not None


def test_httpd_service_build_image():
    """
    Test that the httpd service can build an image.
    """
    # Render the build
    walker = TreeRenderer()
    walker.walk(config_service.config.build_paths, config_service.config)
    image_id, build_output = httpd_service.build_image(LATEST_IMAGE)
    assert image_id is not None
    for line in build_output:
        print(line)


def test_httpd_service_run_container():
    """
    Test that the httpd service can run a container.
    """
    httpd_container = httpd_service.run_container(LATEST_IMAGE, "httpd-nexus")
    assert httpd_container is not None
    assert httpd_service.is_container_running(httpd_container.id)


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
    domain = config_service.config.admin.domain
    assert healthcheck(domain)


def test_podman_rm_container():
    """
    Test that the podman service can remove a container.
    """
    container_id = httpd_service.get_container_id("httpd-nexus")
    assert container_id is not None
    if httpd_service.is_container_running(container_id):
        httpd_service.stop_container(container_id)
    httpd_service.remove_container(container_id)
    container_id = httpd_service.get_container_id("httpd-nexus")
    assert container_id is None


def test_podman_rm_image():
    """
    Test that the podman service can remove an image.
    """
    image = "httpd-nexus:latest"
    httpd_service.remove_image(image)
    image_id = httpd_service.get_image_id(image)
    assert image_id is None
