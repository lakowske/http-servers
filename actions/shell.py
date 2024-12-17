"""
This module starts an IPython shell with the necessary imports and services available.
"""

from IPython import start_ipython
from configuration.container import ServerContainer

container = ServerContainer()
config_service = container.config_service()
config_service.load_yaml_config("secrets/config.yaml")
podman_service = container.podman_service()
httpd_service = container.httpd_service()
user_service = container.user_service()


def ipython_shell():
    """
    Start an IPython shell with the necessary imports and services available.
    """
    start_ipython(
        argv=[],
        user_ns={
            "config_service": config_service,
            "podman_service": podman_service,
            "httpd_service": httpd_service,
            "user_service": user_service,
        },
    )
