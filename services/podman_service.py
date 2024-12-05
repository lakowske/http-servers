"""
This module provides a service for interacting with Podman containers.
"""

from typing import List, Tuple
import podman
from podman.domain.containers import Container
from configuration.app import PodmanConfig


def filter_none_kwargs(**kwargs):
    """
    Filters out keyword arguments with None values.

    Args:
        **kwargs: Arbitrary keyword arguments.

    Returns:
        dict: A dictionary containing only the key-value pairs from kwargs where the value is not None.
    """
    return {k: v for k, v in kwargs.items() if v is not None}


class PodmanService:
    """
    A service class to interact with Podman containers using a provided configuration.
    Attributes:
        podman_config (PodmanConfig): Configuration object for Podman connection.
    Methods:
        get_client():
            Creates and returns a Podman client instance using the provided configuration.
        list_containers():
            Lists all containers managed by the Podman client.
    """

    def __init__(self, podman_config: PodmanConfig):
        self.podman_config = podman_config

    def get_client(self) -> podman.PodmanClient:
        """
        Creates and returns a PodmanClient instance with the configuration specified in podman_config.

        Returns:
            podman.PodmanClient: A configured Podman client instance.
        """
        return podman.PodmanClient(
            **filter_none_kwargs(
                base_url=self.podman_config.socket_url,
                timeout=self.podman_config.timeout,
                tls_verify=self.podman_config.tls_verify,
                cert_path=self.podman_config.cert_path,
            )
        )

    def list_containers(self):
        """
        List all containers.

        This method retrieves a list of all containers using the client obtained
        from the `get_client` method.

        Returns:
            list: A list of container objects.
        """
        with self.get_client() as client:
            return client.containers.list()

    def build_image(
        self, path: str, dockerfile: str, tag: str
    ) -> Tuple[str, List[str]]:
        """
        Build an image.

        This method builds an image using the client obtained from the `get_client` method.

        Returns:
            list: A list of image objects.
        """
        with self.get_client() as client:
            return client.images.build(path=path, dockerfile=dockerfile, tag=tag)

    def rm_image(self, image_id: str):
        """
        Remove an image if it exists.

        This method removes an image using the client obtained from the `get_client` method.

        Returns:
            list: A list of image objects.
        """
        if self.get_image_id(image_id) is None:
            return None
        with self.get_client() as client:
            return client.images.remove(image_id)

    def run_container(
        self,
        image: str,
        name: str,
        ports: dict,
        mounts: List,
        environment: dict,
        detach: bool = True,
    ) -> Container:
        """
        Run a container.

        This method runs a container using the client obtained from the `get_client` method.

        Returns:
            list: A list of container objects.
        """
        with self.get_client() as client:
            return client.containers.run(
                image=image,
                name=name,
                ports=ports,
                mounts=mounts,
                environment=environment,
                detach=detach,
            )

    def exec_container(self, container_id: str, command: str):
        """
        Execute a command in a container.

        This method executes a command in a container using the client obtained from the `get_client` method.

        Returns:
            list: A list of container objects.
        """
        with self.get_client() as client:
            return client.containers.get(container_id).exec_run(cmd=command)

    def get_container_id(self, container_name: str):
        """
        Get the container ID.

        This method retrieves the container ID using the client obtained from the `get_client` method.

        Returns:
            str: The container ID.
        """
        with self.get_client() as client:
            try:
                return client.containers.get(container_name).id
            except podman.errors.NotFound:
                return None

    def get_image_id(self, image_name: str):
        """
        Get the image ID.

        This method retrieves the image ID using the client obtained from the `get_client` method.

        Returns:
            str: The image ID.
        """
        with self.get_client() as client:
            try:
                return client.images.get(image_name).id
            except podman.errors.exceptions.ImageNotFound:
                return None

    def stop_container(self, container_id: str):
        """
        Stop a container.

        This method stops a container using the client obtained from the `get_client` method.

        Returns:
            list: A list of container objects.
        """
        with self.get_client() as client:
            return client.containers.get(container_id).stop()

    def rm_container(self, container_id: str):
        """
        Remove a container.

        This method removes a container using the client obtained from the `get_client` method.

        Returns:
            list: A list of container objects.
        """
        with self.get_client() as client:
            return client.containers.get(container_id).remove()

    def is_container_running(self, container_id: str):
        """
        Check if a container is running.

        This method checks if a container is running using the client obtained from the `get_client` method.

        Returns:
            bool: True if the container is running, False otherwise.
        """
        with self.get_client() as client:
            return client.containers.get(container_id).status == "running"
