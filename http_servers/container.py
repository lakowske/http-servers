from .config_loader import ConfigurationLoader, load_configs
from dependency_injector import containers, providers
from .config_schema import PodmanConfig
from podman.client import PodmanClient


def create_podman_config(config):
    return PodmanConfig(
        socket_url=config["podman"].get("socket_url", None),
        timeout=config["podman"].get("timeout", 30),
        tls_verify=config["podman"].get("tls_verify", True),
        cert_path=config["podman"].get("cert_path", None),
    )


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    loaded_configs = providers.Factory(load_configs, config_path="config.yaml")

    podman_config = providers.Callable(create_podman_config, config=loaded_configs)
