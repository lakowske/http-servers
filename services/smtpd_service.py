from configuration.app import WORKSPACE
from services.podman_service import PodmanService
from services.config_service import ConfigService

LATEST_IMAGE = "smtpd-nexus:latest"
DEFAULT_CONTAINER_NAME = "smtpd-nexus"


class SmtpdService:
    """
    A service class to interact with a Podman smtpd container using a provided configuration.
    """

    def __init__(self, podman_service: PodmanService, config_service: ConfigService):
        self.podman_service = podman_service

        self.build_paths = config_service.config.build_paths
        self.mail_path = self.build_paths.get("mail").tree_root_path(WORKSPACE)
        self.smtpd_dockerfile_path = (
            config_service.config.build_paths.get("mail")
            .get("Dockerfile")
            .tree_root_path(WORKSPACE)
        )

    def build_image(self, tag: str):
        """
        Build an image.

        This method builds an new image with the provided tag.
        """
        return self.podman_service.build_image(
            path=self.mail_path, dockerfile=self.smtpd_dockerfile_path, tag=tag
        )

    def run_container(self, tag: str, name: str):
        """
        Run the mail server container.
        """
        volumes = {
            "maildata": {"bind": "/var/mail", "mode": "rw"},
        }
        ports = {"25/tcp": 25, "587/tcp": 587, "993/tcp": 993}
        with self.podman_service.get_client() as client:
            container = client.containers.run(
                tag,
                name=name,
                detach=True,
                ports=ports,
                volumes=volumes,
            )
            return container

    def stop_container(self, container_id: str):
        """
        Stop the mail server container.
        """
        self.podman_service.stop_container(container_id)

    def remove_container(self, container_id: str):
        """
        Remove the mail server container.
        """
        self.podman_service.rm_container(container_id)

    def remove_image(self, image_id: str):
        """
        Remove the mail server image.
        """
        self.podman_service.rm_image(image_id)

    def get_container_id(self, name: str):
        """
        Get the container id.
        """
        return self.podman_service.get_container_id(name)

    def is_container_running(self, container_id: str):
        """
        Check if a container is running.
        """
        return self.podman_service.is_container_running(container_id)
