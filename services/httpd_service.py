"""
This module provides a service for interacting with a Podman httpd container.
"""

from podman.domain.containers import Container
from services.config_service import ConfigService
from services.podman_service import PodmanService
from configuration.app import WORKSPACE

LATEST_IMAGE = "httpd-nexus:latest"
DEFAULT_CONTAINER_NAME = "httpd-nexus"


class HttpdService:
    """
    A service class to interact with a Podman httpd container using a provided configuration.
    """

    def __init__(self, podman_service: PodmanService, config_service: ConfigService):
        self.podman_service = podman_service

        self.build_paths = config_service.config.build_paths
        self.webroot_path = self.build_paths.get("webroot").tree_root_path(WORKSPACE)
        self.cgi_path = self.build_paths.get("cgi").tree_root_path(WORKSPACE)
        self.httpd_config_path = (
            config_service.config.build_paths.get("apache")
            .get("conf")
            .get("httpd.conf")
            .tree_root_path(WORKSPACE)
        )
        self.ssl_config_path = (
            config_service.config.build_paths.get("apache")
            .get("conf")
            .get("extra")
            .get("httpd-ssl.conf")
            .tree_root_path(WORKSPACE)
        )
        self.letsencrypt_path = (
            config_service.config.build_paths.get("apache")
            .get("conf")
            .get("letsencrypt")
            .tree_root_path(WORKSPACE)
        )
        self.scripts_path = (
            config_service.config.build_paths.get("apache")
            .get("scripts")
            .tree_root_path(WORKSPACE)
        )
        self.git_auth_path = (
            config_service.config.build_paths.get("apache")
            .get("conf")
            .get("git-auth")
            .tree_root_path(WORKSPACE)
        )

        self.apache_path = config_service.config.build_paths.get(
            "apache"
        ).tree_root_path(WORKSPACE)
        self.apache_dockefile = (
            config_service.config.build_paths.get("apache")
            .get("Dockerfile")
            .tree_root_path(WORKSPACE)
        )

    def run_container(self, image: str, name: str) -> Container:
        """
        Run an httpd container.

        This method runs an httpd container using the client obtained from the `get_client` method.
        """

        container_id = self.podman_service.run_container(
            image=image,
            name=name,
            ports={"80/tcp": 80, "443/tcp": 443},
            mounts=[
                {
                    "target": "/usr/local/apache2/htdocs",
                    "source": self.webroot_path,
                    "type": "bind",
                    "read_only": False,
                },
                {
                    "target": "/usr/local/apache2/cgi-bin",
                    "source": self.cgi_path,
                    "type": "bind",
                    "read_only": False,
                },
                {
                    "target": "/usr/local/apache2/conf/letsencrypt",
                    "source": self.letsencrypt_path,
                    "type": "bind",
                    "read_only": False,
                },
                {
                    "target": "/usr/local/apache2/scripts",
                    "source": self.scripts_path,
                    "type": "bind",
                    "read_only": False,
                },
                {
                    "target": "/usr/local/apache2/conf/httpd.conf",
                    "source": self.httpd_config_path,
                    "type": "bind",
                    "read_only": False,
                },
                {
                    "target": "/usr/local/apache2/conf/extra/httpd-ssl.conf",
                    "source": self.ssl_config_path,
                    "type": "bind",
                    "read_only": False,
                },
                {
                    "target": "/usr/local/apache2/conf/git-auth",
                    "source": self.git_auth_path,
                    "type": "bind",
                    "read_only": False,
                },
            ],
            environment={},
        )
        return container_id

    def reload_configuration(self, container_id: str):
        """
        Reload the configuration.

        This method reloads the configuration of the container with the provided container_id.
        """
        self.podman_service.exec_container(container_id, "httpd -k graceful")

    def build_image(self, tag: str):
        """
        Build an image.

        This method builds an new image with the provided tag.
        """
        return self.podman_service.build_image(
            path=self.apache_path, dockerfile=self.apache_dockefile, tag=tag
        )

    def is_container_running(self, container_id: str):
        """
        Check if a container is running.

        This method checks if the container with the provided container_id is running.
        """
        return self.podman_service.is_container_running(container_id)

    def stop_container(self, container_id: str):
        """
        Stop a container.

        This method stops the container with the provided container_id.
        """
        self.podman_service.stop_container(container_id)

    def remove_container(self, container_id: str):
        """
        Remove a container.

        This method removes the container with the provided container_id.
        """
        self.podman_service.rm_container(container_id)

    def remove_image(self, image: str):
        """
        Remove an image.

        This method removes the image with the provided image.
        """
        return self.podman_service.rm_image(image)

    def get_container_id(self, name: str):
        """
        Get the container id.

        This method returns the container id of the container with the provided name.
        """
        return self.podman_service.get_container_id(name)

    def get_image_id(self, image: str):
        """
        Get the image id.

        This method returns the image id of the image with the provided name.
        """
        return self.podman_service.get_image_id(image)
