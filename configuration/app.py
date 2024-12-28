"""
This module contains the configuration classes for the server.
"""

import os
from typing import List, Optional
from pydantic import BaseModel, Field

from configuration.tree_nodes import FSTree, AdminContext, container_paths, build_tree

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


class Runtime(BaseModel):
    """Runtime is a configuration class for the server runtime"""

    withinContainer: bool = (
        False  # Whether the app is running within the httpd container, or on the host
    )


class BuildContext(BaseModel):
    """BuildContext is a configuration for the artifact build process"""

    build_root: str = "."
    template_root: str = "templates"


class ImapConfig(BaseModel):
    """ImapConfig is a configuration class for the IMAP server"""

    server: str = "localhost"
    port: int = 1143
    username: Optional[str] = None
    password: Optional[str] = None


class SmtpConfig(BaseModel):
    """SmtpConfig is a configuration class for the SMTP server"""

    server: str = "localhost"
    port: int = 1025
    sender_email: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


class HttpReverseProxy(BaseModel):
    """
    HttpReverseProxy is a configuration class for a http reverse proxy entry,
    which is a mapping from a URL to a backend http server that will handle the request
    """

    url: str  # The URL to match (e.g. /api/login, /app/email, etc...)
    backend: str  # The URL to forward the request to (e.g. http://localhost:8080)


class Config(BaseModel):
    """Main server configuration"""

    admin: AdminContext
    runtime: Runtime = Runtime()
    podman: PodmanConfig = PodmanConfig()
    imap: ImapConfig = ImapConfig()
    smtp: SmtpConfig = SmtpConfig()
    proxies: List[HttpReverseProxy] = []
    build: BuildContext = BuildContext()
    container_paths: FSTree = container_paths
    build_paths: FSTree = build_tree

    def to_kwargs(self) -> dict:
        """Convert the configuration to a dictionary"""

        kwargs = {
            **self.admin.model_dump(),
            **self.build.model_dump(),
            **self.model_dump(),
        }
        return kwargs
