from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PodmanConfig:
    """
    PodmanConfig is a configuration class for Podman.

    Attributes:
        socket_url (str): The URL of the Podman socket.
        timeout (int): The timeout value for Podman operations.
        tls_verify (bool): Whether to verify TLS certificates.
        cert_path (Optional[str]): The path to the TLS certificates, if any.
    """

    socket_url: str
    timeout: int
    tls_verify: bool
    cert_path: Optional[str] = None


@dataclass
class ContainerPaths:
    """Container path configuration"""

    webroot: str = "/usr/local/apache2/htdocs"
    ssl_config: str = "/usr/local/apache2/conf/extra/httpd-ssl.conf"
    cgi_bin: str = "/usr/local/apache2/cgi-bin"
    letsencrypt: str = "/usr/local/apache2/conf/letsencrypt"


@dataclass
class BuildPaths:
    """Build directory path configuration"""

    root: str = "build"
    apache: str = "build/apache"
    certbot: str = "build/certbot"
    webroot: str = "build/webroot"
    secrets: str = "build/secrets"


@dataclass
class ServerConfig:
    """Server configuration settings"""

    domain: str = "localhost"
    email: Optional[str] = None
    paths: BuildPaths = field(default_factory=BuildPaths)
    container_paths: ContainerPaths = field(default_factory=ContainerPaths)

    def __post_init__(self):
        if self.email is None:
            self.email = f"admin@{self.domain}"
