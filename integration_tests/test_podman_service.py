"""
Integration tests for the podman service.
"""

from configuration.container import ServerContainer
from actions.build import (
    build_images,
    build_httpd_image,
    build_mail_image,
    build,
    render,
    list_containers,
    run_httpd_container,
    run_mail_container,
    health,
    reload_httpd,
    rm_httpd_container,
    rm_mail_container,
    rm_httpd_image,
    rm_mail_image,
    create_mail_volume,
    remove_mail_volume,
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


def test_build_images():
    """
    Test that the podman service can build an image.
    """
    build_images()


def test_build_httpd_image():
    """
    Test that the podman service can build the httpd image.
    """
    image_id = build_httpd_image()
    assert image_id is not None


def test_build_mail_image():
    """
    Test that the podman service can build the mail image.
    """
    image_id = build_mail_image()
    assert image_id is not None


def test_mail_volume_creation():
    """
    Test that the podman service can create a mail volume.
    """
    # Assuming you have a similar function for the mail service
    # create_mail_volume() or similar

    create_mail_volume()


def test_mail_volume_removal():
    """
    Test that the podman service can remove a mail volume.
    """
    # Assuming you have a similar function for the mail service
    # remove_mail_volume() or similar

    remove_mail_volume()


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
    run_httpd_container()


def test_mail_service_run_container():
    """
    Test that the mail service can run a container.
    """
    # Assuming you have a similar function for the mail service
    # run_mail_container() or similar

    run_mail_container()


def test_reload():
    """
    Test that the httpd service can reload the configuration of a container.
    """
    reload_httpd()


def test_http_healthcheck():
    """
    Test that the podman service can perform an http healthcheck on a
    container.
    """
    health()


def test_rm_httpd_container():
    """
    Test that the podman service can remove a container.
    """
    rm_httpd_container()


def test_rm_mail_container():
    """
    Test that the podman service can remove a mail container.
    """
    rm_mail_container()


def test_rm_httpd_image():
    """
    Test that the podman service can remove an image.
    """
    rm_httpd_image()


def test_rm_mail_image():
    """
    Test that the podman service can remove a mail image.
    """
    rm_mail_image()
