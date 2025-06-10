"""
A podman service provides some service (httpd, mail, etc...) using Podman to
manage the service containers.  This is often used as a base class for specific
services like HttpdService or MailService, which implement specific
functionality.
"""

from services.config_service import ConfigService
from services.podman_client_service import PodmanClientService


class PodmanService:
    """
    A base class for Podman services that provides common functionality for
    managing Podman containers.
    """

    def __init__(
        self,
        podman_client_service: PodmanClientService,
        config_service: ConfigService,
    ):
        self.podman_service = podman_client_service
        self.config_service = config_service

    def get_containers(self):
        """
        Get a list of all containers managed by this service.
        """
        return self.podman_service.get_all_containers()

    def is_container_running(self, container_id: str):
        """
        Check if a container is running.

        This method checks if the container with the provided container_id is
        running.
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

    def get_container_id(self, name: str):
        """
        Get the container id.

        This method returns the container id of the container with the provided
        name.
        """
        return self.podman_service.get_container_id(name)

    def get_image_id(self, image: str):
        """
        Get the image id.

        This method returns the image id of the image with the provided name.
        """
        return self.podman_service.get_image_id(image)

    def remove_image(self, image: str):
        """
        Remove an image.

        This method removes the image with the provided image.
        """
        return self.podman_service.rm_image(image)
