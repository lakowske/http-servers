from dataclasses import dataclass
from typing import Optional

@dataclass
class PodmanConfig:
    socket_url: str
    timeout: int
    tls_verify: bool
    cert_path: Optional[str] = None