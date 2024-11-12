from dependency_injector.wiring import inject, Provide
from .container import Container
import podman


class PodmanService:
    @inject
    def __init__(
        self, podman_client: podman.PodmanClient = Provide[Container.podman_client]
    ):
        self.client = podman_client.provider()

    def list_containers(self):
        with self.client as client:
            return client.containers.list()
