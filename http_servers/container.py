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


def filter_none_kwargs(**kwargs):
    return {k: v for k, v in kwargs.items() if v is not None}


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    loaded_configs = providers.Singleton(load_configs, config_path="config.yaml")

    podman_config = providers.Singleton(create_podman_config, config=loaded_configs)

    podman_client = providers.Singleton(
        PodmanClient,
        **filter_none_kwargs(
            base_url=podman_config().socket_url,
            timeout=podman_config().timeout,
            tls_verify=podman_config().tls_verify,
            cert_path=podman_config().cert_path,
        )
    )

    def load_config(self):
        self.config.from_dict(self.config_loader().load_configs("config.yaml"))
