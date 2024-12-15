"""
Can do the following actions:
1. Renders the configuration tree into a build directory
2. Builds the image using the build directory
3. Runs the container
4. Does a health check on the container
5. Runs certbot to get a certificates from Let's Encrypt
6. Reloads the configuration

"""

import argparse
import inspect
import sys
from configuration.tree_walker import TreeRenderer
from configuration.container import ServerContainer
from services.httpd_service import (
    LATEST_IMAGE,
    DEFAULT_CONTAINER_NAME,
    GIT_REPO_VOLUME,
    GIT_TEST_REPO,
)
from http_server.health_check import healthcheck


container = ServerContainer()
config_service = container.config_service()
config_service.load_yaml_config("secrets/config.yaml")
podman_service = container.podman_service()
httpd_service = container.httpd_service()


def list_containers():
    """
    List all containers
    """
    containers = podman_service.list_containers()
    for podman_container in containers:
        print(f'{podman_container.name} {podman_container.attrs["State"]}')
    return containers


def render():
    """
    Render the configuration tree into a build directory
    """
    walker = TreeRenderer()
    walker.walk(config_service.config.build_paths, config_service.config)


def build_image():
    """
    Build the image using the configuration found in secrets/config.yaml
    """
    image_id, build_output = httpd_service.build_image(LATEST_IMAGE)
    assert image_id is not None
    for line in build_output:
        print(line)


def build():
    """
    Build the image using the configuration found in secrets/config.yaml
    """
    render()
    build_image()


def run_container():
    """
    Run the container using the image built in the build step
    """
    httpd_container = httpd_service.run_container(LATEST_IMAGE, DEFAULT_CONTAINER_NAME)
    assert httpd_container is not None
    assert httpd_service.is_container_running(httpd_container.id)


def health():
    """
    Check the health of the container
    """
    domain = config_service.config.admin.domain
    assert healthcheck(domain)


def certificates():
    """
    Get certificates from Let's Encrypt
    """
    certbot = container.certbot_service()
    success = certbot.create_certificate(
        config_service.config.admin.domain, dry_run=False, staging=False
    )
    assert success is True


def reload_httpd():
    """
    Reload the http server configuration
    """
    container_id = httpd_service.get_container_id(DEFAULT_CONTAINER_NAME)
    assert container_id is not None
    httpd_service.reload_configuration(container_id)
    assert httpd_service.is_container_running(container_id)


def create_git_repo_volume():
    """
    Create a git repo volume
    """
    httpd_service.create_git_repo_volume(GIT_REPO_VOLUME)


def remove_git_repo_volume():
    """
    Remove the git repo volume
    """
    httpd_service.remove_git_repo_volume(GIT_REPO_VOLUME)


def create_test_repo():
    """
    Create a test git repo
    """
    container_id = httpd_service.get_container_id(DEFAULT_CONTAINER_NAME)
    assert container_id is not None
    httpd_service.create_git_repo(container_id, GIT_TEST_REPO)


def reload():
    """
    Reload the configuration
    """
    certbot = container.certbot_service()
    success = certbot.update_apache_configs_to_letsencrypt(
        config_service.config.admin.domain
    )
    assert success
    container_id = httpd_service.get_container_id(DEFAULT_CONTAINER_NAME)
    assert container_id is not None
    httpd_service.reload_configuration(container_id)
    assert httpd_service.is_container_running(container_id)


def rm_container():
    """
    Remove the container
    """
    container_id = httpd_service.get_container_id(DEFAULT_CONTAINER_NAME)
    assert container_id is not None
    if httpd_service.is_container_running(container_id):
        httpd_service.stop_container(container_id)
    httpd_service.remove_container(container_id)
    container_id = httpd_service.get_container_id(DEFAULT_CONTAINER_NAME)
    assert container_id is None


def rm_image():
    """
    Remove the image
    """
    image = LATEST_IMAGE
    httpd_service.remove_image(image)
    assert httpd_service.get_image_id(image) is None


def list_functions():
    """
    Introspect the available functions defined in this file and print them to the console
    """
    current_module = sys.modules[__name__]
    functions = inspect.getmembers(current_module, inspect.isfunction)
    function_list = []
    for name, func in functions:
        if func.__module__ == current_module.__name__:
            function_list.append(name)
    return function_list


def usage():
    """
    Print the usage of this script
    """
    print("Usage: python actions/build.py [action]")
    print("Available actions:")
    for action in list():
        print(f"  {action}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage build actions")
    parser.add_argument("action", choices=list_functions(), help="Action to perform")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    if args.verbose:
        print("Verbose mode enabled")
        print(f"Action: {args.action}")

    if args.action in list_functions():
        locals()[args.action]()
    else:
        print(f"Invalid action: {args.action}")
        usage()
