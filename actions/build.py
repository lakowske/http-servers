"""
Can do the following actions:
1. Renders the configuration tree into a build directory
2. Builds the image using the build directory
3. Runs the container
4. Does a health check on the container
5. Runs certbot to get a certificates from Let's Encrypt
6. Reloads the configuration

"""

import uvicorn
from http_server.health_check import healthcheck
from actions.shell import ipython_shell
from actions.dynamic_cli import DynamicCLI
from configuration.tree_walker import TreeRenderer
from configuration.container import ServerContainer
from services.httpd_service import (
    LATEST_IMAGE,
    DEFAULT_HTTPD_CONTAINER_NAME,
    GIT_REPO_VOLUME,
    GIT_TEST_REPO,
    WEBDAV_VOLUME,
)
from services.mail_service import (
    LATEST_IMAGE as MAIL_LATEST_IMAGE,
    DEFAULT_MAIL_CONTAINER_NAME,
    MAIL_VOLUME,
)


cli = DynamicCLI()

container = ServerContainer()
config_service = container.config_service()
config_service.load_yaml_config("secrets/config.yaml")
podman_service = container.podman_service()
httpd_service = container.httpd_service()
mail_service = container.mail_service()
user_service = container.user_service()


@cli.register()
def list_containers():
    """
    List all containers
    """
    containers = podman_service.list_containers()
    for podman_container in containers:
        print(f'{podman_container.name} {podman_container.attrs["State"]}')
    return containers


@cli.register()
def render():
    """
    Render the configuration tree into a build directory
    """
    walker = TreeRenderer()
    walker.walk(config_service.config.build_paths, config_service.config)


@cli.register()
def build_images():
    """
    Build the image using the configuration found in secrets/config.yaml
    """
    # Build httpd image
    build_httpd_image()
    # Build mail image
    build_mail_image()


@cli.register()
def build_httpd_image():
    """
    Build the httpd image using the configuration found in secrets/config.yaml
    """
    image_id, build_output = httpd_service.build_image(LATEST_IMAGE)
    assert image_id is not None
    for line in build_output:
        print(line)
    return image_id


@cli.register()
def build_mail_image():
    """
    Build the mail image using the configuration found in secrets/config.yaml
    """
    image_id, build_output = mail_service.build_image(MAIL_LATEST_IMAGE)
    assert image_id is not None
    for line in build_output:
        print(line)
    return image_id


@cli.register()
def build():
    """
    Build the image using the configuration found in secrets/config.yaml
    """
    render()
    build_images()


@cli.register()
def run_httpd_container():
    """
    Run the container using the image built in the build step
    """
    httpd_container = httpd_service.run_container(LATEST_IMAGE, DEFAULT_HTTPD_CONTAINER_NAME)
    assert httpd_container is not None
    assert httpd_service.is_container_running(httpd_container.id)


@cli.register()
def run_mail_container():
    """
    Run the mail container using the image built in the build step
    """
    mail_container = mail_service.run_container(MAIL_LATEST_IMAGE, DEFAULT_MAIL_CONTAINER_NAME)
    assert mail_container is not None
    assert mail_service.is_container_running(mail_container.id)


@cli.register()
def health():
    """
    Check the health of the container
    """
    domain = config_service.config.admin.domain
    assert healthcheck(domain)


@cli.register()
def certificates():
    """
    Get certificates from Let's Encrypt
    """
    certbot = container.certbot_service()
    success = certbot.create_certificate(config_service.config.admin.domain, dry_run=False, staging=False)
    assert success is True


@cli.register()
def reload_httpd():
    """
    Reload the http server configuration
    """
    container_id = httpd_service.get_container_id(DEFAULT_HTTPD_CONTAINER_NAME)
    assert container_id is not None
    httpd_service.reload_configuration(container_id)
    assert httpd_service.is_container_running(container_id)


@cli.register()
def create_mail_volume():
    """
    Create a mail volume
    """
    mail_service.create_mail_volume(MAIL_VOLUME)


@cli.register()
def remove_mail_volume():
    """
    Remove the mail volume
    """
    mail_service.remove_mail_volume(MAIL_VOLUME)


@cli.register()
def create_git_repo_volume():
    """
    Create a git repo volume
    """
    httpd_service.create_repo_volume(GIT_REPO_VOLUME)


@cli.register()
def remove_git_repo_volume():
    """
    Remove the git repo volume
    """
    httpd_service.remove_repo_volume(GIT_REPO_VOLUME)


@cli.register()
def create_webdav_volume():
    """
    Create a webdav volume
    """
    httpd_service.create_repo_volume(WEBDAV_VOLUME)


@cli.register()
def remove_webdav_volume():
    """
    Remove the webdav volume
    """
    httpd_service.remove_repo_volume(WEBDAV_VOLUME)


@cli.register()
def create_test_repo():
    """
    Create a test git repo
    """
    container_id = httpd_service.get_container_id(DEFAULT_HTTPD_CONTAINER_NAME)
    assert container_id is not None
    httpd_service.create_git_repo(container_id, GIT_TEST_REPO)


@cli.register()
def reload():
    """
    Reload the configuration
    """
    certbot = container.certbot_service()
    success = certbot.update_apache_configs_to_letsencrypt(config_service.config.admin.domain)
    assert success
    container_id = httpd_service.get_container_id(DEFAULT_HTTPD_CONTAINER_NAME)
    assert container_id is not None
    httpd_service.reload_configuration(container_id)
    assert httpd_service.is_container_running(container_id)


@cli.register()
def rm_httpd_container():
    """
    Remove the container
    """
    container_id = httpd_service.get_container_id(DEFAULT_HTTPD_CONTAINER_NAME)
    assert container_id is not None
    if httpd_service.is_container_running(container_id):
        httpd_service.stop_container(container_id)
    httpd_service.remove_container(container_id)
    container_id = httpd_service.get_container_id(DEFAULT_HTTPD_CONTAINER_NAME)
    assert container_id is None


@cli.register()
def rm_mail_container():
    """
    Remove the mail container
    """
    container_id = mail_service.get_container_id(DEFAULT_MAIL_CONTAINER_NAME)
    assert container_id is not None
    if mail_service.is_container_running(container_id):
        mail_service.stop_container(container_id)
    mail_service.remove_container(container_id)
    container_id = mail_service.get_container_id(DEFAULT_MAIL_CONTAINER_NAME)
    assert container_id is None


@cli.register()
def rm_httpd_image():
    """
    Remove the httpd image
    """
    image = LATEST_IMAGE
    httpd_service.remove_image(image)
    assert httpd_service.get_image_id(image) is None


@cli.register()
def rm_mail_image():
    """
    Remove the mail image
    """
    image = MAIL_LATEST_IMAGE
    mail_service.remove_image(image)
    assert mail_service.get_image_id(image) is None


@cli.register()
def git_password():
    """
    Generate a new password
    """
    password = user_service.random_password("git")
    print(password)
    return password


@cli.register()
def run_ops():
    """
    Run the operations http server.
    """
    uvicorn.run(
        "web.home:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=["./templates", "./templates/web"],
        reload_includes=["*.html"],
    )


@cli.register()
def run_shell():
    """
    Run an IPython shell
    """
    ipython_shell()


if __name__ == "__main__":
    cli.parse_and_call()
