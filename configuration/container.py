"""
This module provides a services for testing and application use.
"""

from dependency_injector import containers, providers
from configuration.config_loader import load_configs
from configuration.tree_nodes import AdminContext
from configuration.app import PodmanConfig, Config
from services.podman_service import PodmanService
from services.mail_service import MailService
from services.config_service import ConfigService


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


def create_app_config(config) -> Config:
    """
    Creates an AppConfig object from a configuration dictionary.
    """
    # Global configuration instance
    app_config = Config(
        admin_context=AdminContext(
            domain="example.com",
            email="admin@example.com",
        )
    )
    return app_config


def create_mail_service(app_config: Config) -> MailService:
    """
    Creates a MailService object from an AppConfig object.
    """
    return MailService(
        imap=app_config.imap,
        smtp=app_config.smtp,
    )


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

    loaded_configs = providers.Factory(load_configs, config_path="config.yaml")

    app_config = providers.Singleton(create_app_config, config=loaded_configs)

    podman_config = providers.Singleton(create_podman_config, config=loaded_configs)

    config_service = providers.Singleton(create_config_service)

    podman_service = providers.Factory(PodmanService, podman_config=podman_config)

    email_service = providers.Factory(
        create_mail_service,
        app_config=app_config,
    )
