"""
This module provides a services for testing and application use.
"""

from dependency_injector import containers, providers
from configuration.config_loader import load_configs
from configuration.tree_nodes import AdminContext
from configuration.app import PodmanConfig, Config
from configuration.app import ImapConfig
from configuration.app import SmtpConfig
from services.podman_service import PodmanService
from services.config_service import ConfigService
from mail.imap import ImapService
from mail.smtp import SmtpService


def create_podman_config(config) -> PodmanConfig:
    """
    Creates a PodmanConfig object from a configuration dictionary.
    """
    return PodmanConfig(
        socket_url=config["podman"].get("socket_url", None),
        timeout=config["podman"].get("timeout", 30),
        tls_verify=config["podman"].get("tls_verify", True),
        cert_path=config["podman"].get("cert_path", None),
    )


def create_imap_service(config_service: ConfigService) -> ImapService:
    """
    Creates an ImapService object from an AppConfig object.
    """
    return ImapService(config_service.config.imap)


def to_imap_config(config_service: ConfigService) -> ImapConfig:
    """
    Converts a ConfigService object to an ImapConfig object.
    """
    return config_service.config.imap


def to_smtp_config(config_service: ConfigService) -> SmtpConfig:
    """
    Converts a ConfigService object to an SmtpConfig object.
    """
    return config_service.config.smtp


def to_podman_config(config_service: ConfigService) -> PodmanConfig:
    """
    Converts a ConfigService object to an PodmanConfig object.
    """
    return config_service.config.podman


def create_config_service() -> ConfigService:
    """
    Creates a ConfigService object.
    """

    config = Config(
        admin_context=AdminContext(
            domain="example.com",
            email="admin@example.com",
        )
    )

    return ConfigService(config=config)


class ServerContainer(containers.DeclarativeContainer):
    """
    Dependency injection container for configuration loading
    """

    config = providers.Configuration()

    config_service = providers.Singleton(create_config_service)

    podman_config = providers.Singleton(to_podman_config, config_service=config_service)

    imap_config = providers.Factory(to_imap_config, config_service=config_service)

    smtp_config = providers.Factory(to_smtp_config, config_service=config_service)

    podman_service = providers.Factory(PodmanService, podman_config=podman_config)

    imap_service = providers.Singleton(ImapService, imap_config=imap_config)

    smtp_service = providers.Singleton(SmtpService, smtp_config=smtp_config)
