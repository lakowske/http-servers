import os
from pydantic import BaseModel, Field

from typing import Optional
from configuration.tree import FSTree, container_paths, build

# Create an absolute workspace directory variable
MODULE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.dirname(MODULE)


class PodmanConfig(BaseModel):
    """
    PodmanConfig is a configuration class for Podman.

    Attributes:
        socket_url (str): The URL of the Podman socket.
        timeout (int): The timeout value for Podman operations.
        tls_verify (bool): Whether to verify TLS certificates.
        cert_path (Optional[str]): The path to the TLS certificates, if any.
    """

    socket_url: Optional[str] = Field(default=None, description="Path to Podman socket")
    timeout: Optional[int] = Field(
        default=30, description="Timeout value for Podman operations"
    )
    tls_verify: Optional[bool] = Field(
        default=False, description="Verify TLS certificates"
    )
    cert_path: Optional[str] = Field(
        default=None, description="Path to TLS certificates"
    )


class Config(BaseModel):
    """Main configuration"""

    domain: str
    email: Optional[str] = None
    container: FSTree = container_paths
    build_paths: FSTree = build
    podman: PodmanConfig = PodmanConfig()
