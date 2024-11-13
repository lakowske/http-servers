from dependency_injector.wiring import inject, Provide
from .config_schema import PodmanConfig

import podman

def filter_none_kwargs(**kwargs):
    return {k: v for k, v in kwargs.items() if v is not None}

class PodmanService:
    def __init__(self, podman_config: PodmanConfig):
        self.podman_config = podman_config

    def get_client(self):
        return podman.PodmanClient(**filter_none_kwargs(
            base_url=self.podman_config.socket_url,
            timeout=self.podman_config.timeout,
            tls_verify=self.podman_config.tls_verify,
            cert_path=self.podman_config.cert_path)
        )
    
    def list_containers(self):
        with self.client as client:
            return client.containers.list()
