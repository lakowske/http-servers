"""
This module provides a service for interacting with Podman containers.
"""

from typing import List, Tuple
import podman
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

    def run_container(
        self,
        image: str,
        name: str,
        ports: dict,
        mounts: List,
        environment: dict,
        detach: bool = True,
    ):
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
