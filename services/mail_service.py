"""
This module provides a service to handle interacting with a Podman email
sending and receiving service.
"""

from podman.domain.containers import Container
from services.config_service import ConfigService
from services.podman_client_service import PodmanClientService
from services.podman_service import PodmanService
from configuration.app import WORKSPACE


LATEST_IMAGE = "mail-nexus:latest"
DEFAULT_MAIL_CONTAINER_NAME = "mail-nexus"
MAIL_VOLUME = "mail"


class MailService(PodmanService):
    """A service to handle email sending and receiving."""

    def __init__(
        self,
        podman_service: PodmanClientService,
        config_service: ConfigService,
    ):
        """Initialize the MailService with Podman and Config services.
        Args:
            podman_service (PodmanClientService): The Podman client service.
            config_service (ConfigService): The configuration service.
        """
        super().__init__(podman_service, config_service)

        self.mail_path = config_service.config.build_paths.get("mail").tree_root_path(WORKSPACE)
        self.workspace_path = WORKSPACE
        self.mail_ssl_cert_path = config_service.config.build_paths.get("ssl").tree_root_path(WORKSPACE)
        self.mail_smtp_conf_path = (
            config_service.config.build_paths.get("mail").get("main.cf").tree_root_path(WORKSPACE)
        )
        self.postfix_master_conf_path = (
            config_service.config.build_paths.get("mail").get("master.cf").tree_root_path(WORKSPACE)
        )
        self.mail_dovecot_conf_path = (
            config_service.config.build_paths.get("mail").get("dovecot.conf").tree_root_path(WORKSPACE)
        )
        self.mail_supervisor_conf_path = (
            config_service.config.build_paths.get("mail").get("supervisord.conf").tree_root_path(WORKSPACE)
        )
        self.mail_dockefile = config_service.config.build_paths.get("mail").get("Dockerfile").tree_root_path(WORKSPACE)
        self.letsencrypt_path = (
            config_service.config.build_paths.get("apache").get("conf").get("letsencrypt").tree_root_path(WORKSPACE)
        )
        self.actions_path = WORKSPACE + "/actions"

    def run_container(self, image: str, name: str) -> Container:
        """Run a container with the specified image and name.

        This method runs a container using the provided image and name.
        """
        ports = {
            "25/tcp": 25,  # SMTP
            "143/tcp": 143,  # IMAP
            "465/tcp": 465,  # SMTPS
            "587/tcp": 587,  # SMTP Submission
            "993/tcp": 993,  # IMAPS
        }

        volumes = {
            "mail": {
                "bind": "/var/vmail",
                "mode": "rw",
            },
        }

        mounts = [
            {
                "target": "/usr/local/actions",
                "source": self.actions_path,
                "type": "bind",
                "read_only": False,
            },
            {
                "target": "/etc/ssl/certs/server",
                "source": self.mail_ssl_cert_path,
                "type": "bind",
                "read_only": True,
            },
            {
                "target": "/etc/ssl/certs/letsencrypt",
                "source": self.letsencrypt_path,
                "type": "bind",
                "read_only": True,
            },
            {
                "target": "/etc/postfix/main.cf",
                "source": self.mail_smtp_conf_path,
                "type": "bind",
                "read_only": False,
            },
            {
                "target": "/etc/postfix/master.cf",
                "source": self.postfix_master_conf_path,
                "type": "bind",
                "read_only": False,
            },
            {
                "target": "/etc/dovecot/dovecot.conf",
                "source": self.mail_dovecot_conf_path,
                "type": "bind",
                "read_only": False,
            },
            {
                "target": "/etc/supervisor/supervisord.conf",
                "source": self.mail_supervisor_conf_path,
                "type": "bind",
                "read_only": False,
            },
        ]

        with self.podman_service.get_client() as client:
            container = client.containers.run(
                image=image,
                name=name,
                ports=ports,
                volumes=volumes,
                mounts=mounts,
                detach=True,
                environment={
                    "OVERRIDE_HOSTNAME": (self.config_service.config.admin.domain),
                    "MAIL_DOMAIN": (self.config_service.config.admin.domain),
                    "MAIL_ADMIN_EMAIL": (self.config_service.config.admin.email),
                    "NETWORK_INTERFACE": "",
                    "PERMIT_DOCKER": "host",
                    "LOG_LEVEL": "info",
                    "CONTAINER_NAME": name,
                },
            )
            return container

    def build_image(self, tag: str):
        """
        Build an image.

        This method builds an new image with the provided tag.
        """
        return self.podman_service.build_image(path=self.workspace_path, dockerfile=self.mail_dockefile, tag=tag)

    def create_mail_volume(self, name: str):
        """
        Create a mail volume.

        This method creates a new mail volume with the provided name.
        """
        with self.podman_service.get_client() as client:
            if client.volumes.exists(name):
                return client.volumes.get(name)
            # If the volume does not exist, create it
            client.volumes.create(name=name)

    def remove_mail_volume(self, name: str):
        """
        Remove a mail volume.

        This method removes the mail volume with the provided name.
        """
        with self.podman_service.get_client() as client:
            if client.volumes.exists(name):
                client.volumes.get(name).remove()
            else:
                raise ValueError(f"Volume {name} does not exist.")
