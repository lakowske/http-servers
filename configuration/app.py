"""
This module contains the configuration classes for the server.
"""

import os
from typing import Optional
from pydantic import BaseModel, Field


from configuration.tree_nodes import FSTree, AdminContext, container_paths, build

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


class BuildContext(BaseModel):
    """BuildContext is a configuration class for the build process"""

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


class Config(BaseModel):
    """Main server configuration"""

    admin_context: AdminContext
    imap: ImapConfig = ImapConfig()
    smtp: SmtpConfig = SmtpConfig()
    build_context: BuildContext = BuildContext()
    container: FSTree = container_paths
    build_paths: FSTree = build
    podman: PodmanConfig = PodmanConfig()

    def to_kwargs(self) -> dict:
        """Convert the configuration to a dictionary"""
        kwargs = {**self.admin_context.model_dump(), **self.build_context.model_dump()}
        return kwargs
