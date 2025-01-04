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
import uvicorn
from configuration.tree_walker import TreeRenderer
from configuration.container import ServerContainer
from services.httpd_service import (
    LATEST_IMAGE,
    DEFAULT_CONTAINER_NAME,
    GIT_REPO_VOLUME,
    GIT_TEST_REPO,
    WEBDAV_VOLUME,
)
from services.smtpd_service import (
    LATEST_IMAGE as SMTPD_LATEST_IMAGE,
    DEFAULT_CONTAINER_NAME as SMTPD_DEFAULT_CONTAINER_NAME,
)
from http_server.health_check import healthcheck
from actions.shell import ipython_shell


container = ServerContainer()
config_service = container.config_service()
config_service.load_yaml_config("secrets/config.yaml")
podman_service = container.podman_service()
httpd_service = container.httpd_service()
user_service = container.user_service()
smtpd_service = container.smtpd_service()


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


def build_mail_image():
    """
    Build the image using the configuration found in secrets/config.yaml
    """
    image_id, build_output = smtpd_service.build_image(SMTPD_LATEST_IMAGE)
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


def run_mail_container():
    """
    Run the container using the image built in the build step
    """
    smtpd_container = smtpd_service.run_container(
        SMTPD_LATEST_IMAGE, SMTPD_DEFAULT_CONTAINER_NAME
    )
    assert smtpd_container is not None
    assert smtpd_service.is_container_running(smtpd_container.id)


def rm_mail_container():
    """
    Remove the container
    """
    container_id = smtpd_service.get_container_id(SMTPD_DEFAULT_CONTAINER_NAME)
    assert container_id is not None
    if smtpd_service.is_container_running(container_id):
        smtpd_service.stop_container(container_id)
    smtpd_service.remove_container(container_id)
    container_id = smtpd_service.get_container_id(SMTPD_DEFAULT_CONTAINER_NAME)
    assert container_id is None


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
    httpd_service.create_repo_volume(GIT_REPO_VOLUME)


def remove_git_repo_volume():
    """
    Remove the git repo volume
    """
    httpd_service.remove_repo_volume(GIT_REPO_VOLUME)


def create_webdav_volume():
    """
    Create a webdav volume
    """
    httpd_service.create_repo_volume(WEBDAV_VOLUME)


def remove_webdav_volume():
    """
    Remove the webdav volume
    """
    httpd_service.remove_repo_volume(WEBDAV_VOLUME)


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


def git_password():
    """
    Generate a new password
    """
    password = user_service.random_password("git")
    print(password)
    return password


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


def run_shell():
    """
    Run an IPython shell
    """
    ipython_shell()


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


class CustomHelpFormatter(argparse.HelpFormatter):
    def add_usage(self, usage, actions, groups, prefix=None):
        if prefix is None:
            prefix = "Usage: "
        return super().add_usage(usage, actions, groups, prefix)

    def format_help(self):
        help_text = super().format_help()
        # Customize the actions list
        actions_list = "\n".join(list_functions())
        actions_output = "\n{\n" + actions_list + "\n}"
        help_text = help_text.replace(
            "{" + ",".join(list_functions()) + "}", actions_output
        )
        return help_text


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Manage build actions", formatter_class=CustomHelpFormatter
    )
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
        parser.print_help()
