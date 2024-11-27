"""
This module provides a services for testing and application use.
"""

from dependency_injector import containers, providers
from configuration.config_loader import load_configs
from services.service import PodmanService
from configuration.app import PodmanConfig


def create_podman_config(config):
    """
    Creates a PodmanConfig object from a configuration dictionary.
    """
    return PodmanConfig(
        socket_url=config["podman"].get("socket_url", None),
        timeout=config["podman"].get("timeout", 30),
        tls_verify=config["podman"].get("tls_verify", True),
        cert_path=config["podman"].get("cert_path", None),
    )


class ServerContainer(containers.DeclarativeContainer):
    """
    Dependency injection container for configuration loading
    """

    config = providers.Configuration()

    loaded_configs = providers.Factory(load_configs, config_path="config.yaml")

    podman_config = providers.Singleton(create_podman_config, config=loaded_configs)

    podman_service = providers.Factory(PodmanService, podman_config=podman_config)
