from http_servers.cli import initialize_container
from http_servers.service import PodmanService
from dependency_injector.wiring import inject, Provider
from http_servers.container import ServerContainer
from podman.client import PodmanClient


@inject
def client_provider(client: PodmanClient = Provider[ServerContainer.podman_client]):
    return client.provider()


if __name__ == "__main__":
    # Example YAML configuration file (config.yml):
    """
    podman:
      socket_url: "unix:///run/podman/podman.sock"
      timeout: 30
      tls_verify: true
      cert_path: "/path/to/cert"
    """

    container = initialize_container("config.yml")
    podman_conf = container.podman_config()
    config = container.config()
    podman_client = container.podman_client()
    with container.podman_client() as client:
        print(f"Podman version: {client.version()['Version']}")
    client2 = client_provider()
    with client2 as client:
        print(f"Podman version: {client.version()['Version']}")

    podman_service = PodmanService()
    containers = podman_service.list_containers()
    print(f"Found {len(containers)} containers")
