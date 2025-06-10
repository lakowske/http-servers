"""
This module provides a service for interacting with Podman containers.
"""

from typing import List, Tuple
import subprocess
import json
import podman
from podman.domain.containers import Container
from configuration.app import PodmanConfig


def filter_none_kwargs(**kwargs):
    """
    Filters out keyword arguments with None values.

    Args:
        **kwargs: Arbitrary keyword arguments.

    Returns:
        dict: A dictionary containing only the key-value pairs from kwargs
        where the value is not None.
    """
    return {k: v for k, v in kwargs.items() if v is not None}


class PodmanClientService:
    """
    A service class to interact with Podman containers using a provided
    configuration.

       Attributes:
        podman_config (PodmanConfig): Configuration object for Podman
        connection.
    Methods:
        get_client():
            Creates and returns a Podman client instance using the provided
            configuration.
        list_containers():
            Lists all containers managed by the Podman client.
    """

    def __init__(self, podman_config: PodmanConfig):
        self.podman_config = podman_config

    def get_client(self) -> podman.PodmanClient:
        """
        Creates and returns a PodmanClient instance with the configuration
        specified in podman_config.

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

        This method retrieves a list of all containers using the client
        obtained from the `get_client` method.

        Returns:
            list: A list of container objects.
        """
        with self.get_client() as client:
            return client.containers.list()

    def build_image(self, path: str, dockerfile: str, tag: str) -> Tuple[str, List[str]]:
        """
        Build a container image from a specified path and Dockerfile using CLI for better caching.

        Args:
            path (str): The path to the build context (directory containing the Dockerfile and other resources).
            dockerfile (str): The name of the Dockerfile to use for building the image.
            tag (str): The tag to assign to the built image.

            Tuple[str, List[str]]: The image ID and a list of build output logs.

        Raises:
            subprocess.CalledProcessError: If the podman build command fails.

        Example:
            image_id, logs = build_image('/path/to/context', 'Dockerfile', 'my-image:latest')
        """
        # Use podman CLI for better caching behavior
        cmd = [
            'podman', 'build',
            path,                    # Build context path
            '-f', dockerfile,        # Dockerfile path
            '-t', tag,              # Tag
            '--layers',             # Enable intermediate layer caching
            '--pull=false',         # Don't pull base images unless necessary
        ]
        
        try:
            # Run the command and capture output
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=True,
                cwd=path
            )
            
            # Parse the output lines
            output_lines = []
            if result.stdout:
                output_lines.extend(result.stdout.strip().split('\n'))
            if result.stderr:
                output_lines.extend(result.stderr.strip().split('\n'))
            
            # Get the image ID from the built image
            # Podman outputs the image ID at the end
            image_id = None
            for line in reversed(output_lines):
                if len(line.strip()) == 64:  # SHA256 hash length
                    image_id = line.strip()
                    break
            
            # If we couldn't find the ID in output, get it via inspection
            if not image_id:
                inspect_cmd = ['podman', 'image', 'inspect', tag, '--format', '{{.Id}}']
                inspect_result = subprocess.run(inspect_cmd, capture_output=True, text=True, check=True)
                image_id = inspect_result.stdout.strip()
            
            return image_id, output_lines
            
        except subprocess.CalledProcessError as e:
            # Re-raise with build output for debugging
            error_output = []
            if e.stdout:
                error_output.extend(e.stdout.strip().split('\n'))
            if e.stderr:
                error_output.extend(e.stderr.strip().split('\n'))
            
            raise RuntimeError(f"Podman build failed: {' '.join(e.stderr.split()) if e.stderr else str(e)}") from e

    def rm_image(self, image_id: str):
        """
        Remove an image if it exists.

        This method removes an image using the client obtained from the
        `get_client` method.

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

        This method runs a container using the client obtained from the
        `get_client` method.

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

        This method executes a command in a container using the client obtained
        from the `get_client` method.

        Returns:
            list: A list of container objects.
        """
        with self.get_client() as client:
            return client.containers.get(container_id).exec_run(cmd=command)

    def get_container_id(self, container_name: str):
        """
        Get the container ID.

        This method retrieves the container ID using the client obtained from
        the `get_client` method.

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

        This method retrieves the image ID using the client obtained from the
        `get_client` method.

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

        This method stops a container using the client obtained from the
        `get_client` method.

        Returns:
            list: A list of container objects.
        """
        with self.get_client() as client:
            return client.containers.get(container_id).stop()

    def rm_container(self, container_id: str):
        """
        Remove a container.

        This method removes a container using the client obtained from the
        `get_client` method.

        Returns:
            list: A list of container objects.
        """
        with self.get_client() as client:
            return client.containers.get(container_id).remove()

    def is_container_running(self, container_id: str):
        """
        Check if a container is running.

        This method checks if a container is running using the client obtained
        from the `get_client` method.

        Returns:
            bool: True if the container is running, False otherwise.
        """
        with self.get_client() as client:
            return client.containers.get(container_id).status == "running"
