from fastapi import FastAPI, HTTPException, WebSocket
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, TypeVar, Type
import copy
import json
import yaml
import os


T = TypeVar("T")

# Create an absolute workspace directory variable
WORKSPACE = os.path.dirname(os.path.abspath(__file__))


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


class ContainerPaths(BaseModel):
    """Container path configuration"""

    webroot: str = "/usr/local/apache2/htdocs"
    ssl_config: str = "/usr/local/apache2/conf/extra/httpd-ssl.conf"
    cgi_bin: str = "/usr/local/apache2/cgi-bin"
    letsencrypt: str = "/usr/local/apache2/conf/letsencrypt"


class BuildPaths(BaseModel):
    """Build directory path configuration"""

    root: str = "build"
    apache: str = "apache"
    apache_conf: str = "apache/conf"
    certbot: str = "certbot"
    webroot: str = "webroot"
    secrets: str = "secrets"

    def to_absolute_path(self, path: str) -> str:
        """Convert a relative path to an absolute path"""
        abs_path = f"{WORKSPACE}/{self.root}/{path}"
        return abs_path

    def make_path(self, path: str) -> str:
        """Create a path using the workspace and root directory"""
        abs_path = self.to_absolute_path(path)
        os.makedirs(abs_path, exist_ok=True)
        return abs_path


class Config(BaseModel):
    """Main configuration"""

    domain: str
    email: Optional[str] = None
    container_paths: ContainerPaths = ContainerPaths()
    build_paths: BuildPaths = BuildPaths()
    podman: PodmanConfig = PodmanConfig()


class HostConfig(BaseModel):
    """Configuration for host machine"""

    hostname: str = Field(description="Hostname of the machine")
    ip_address: Optional[str] = Field(default=None, description="Primary IP address")
    cpu_cores: Optional[int] = Field(default=None, description="Number of CPU cores")
    memory_gb: Optional[float] = Field(default=None, description="Total memory in GB")


class ContainerConfig(BaseModel):
    """Configuration for container management"""

    host: HostConfig
    podman: PodmanConfig = PodmanConfig()
    max_containers: Optional[int] = Field(
        default=10, description="Maximum number of containers"
    )
    network_mode: Optional[str] = Field(
        default="bridge", description="Default container network mode"
    )


class APIConfig(BaseModel):
    """Comprehensive API Configuration"""

    domain: str = Field(description="Primary domain name")
    email: str = Field(description="Contact email address")
    container: ContainerConfig

    # Optional additional configuration
    debug_mode: Optional[bool] = Field(default=False, description="Enable debug mode")
    log_level: Optional[str] = Field(default="INFO", description="Logging level")


def copy_merge_config(config: T, update_dict: Dict[str, Any]) -> T:
    """
    Merge a configuration object with a dictionary update

    Args:
        config: Original configuration object
        update_dict: Dictionary containing updates

    Returns:
        Updated configuration object
    """
    # Create a deep copy to avoid modifying the original
    merged_config = copy.deepcopy(config)

    for key, value in update_dict.items():
        # Handle nested dictionaries recursively
        if hasattr(merged_config, key):
            current_value = getattr(merged_config, key)

            # Recursive merge for nested objects
            if isinstance(value, dict) and hasattr(current_value, "__dict__"):
                nested_config = merge_config(current_value, value)
                setattr(merged_config, key, nested_config)
            else:
                # Direct attribute update
                setattr(merged_config, key, value)

    return merged_config


def merge_config(existing_config: BaseModel, update_dict: Dict[str, Any]) -> BaseModel:
    """
    Merge a configuration object with a dictionary update

    Args:
        existing_config: Original configuration object
        update_dict: Dictionary containing updates

    Returns:
        Updated configuration object
    """
    for key, value in update_dict.items():
        if isinstance(value, dict):
            nested_config = getattr(existing_config, key)
            updated_nested_config = merge_config(nested_config, value)
            setattr(existing_config, key, updated_nested_config)
        else:
            setattr(existing_config, key, value)
    return existing_config


def load_config(file_path: str) -> Config:
    """Load configuration from a YAML file"""
    with open(file_path, "r", encoding="utf-8") as file:
        config_data = yaml.safe_load(file)
    return Config(**config_data)


def load_json_config(json_str: str) -> Config:
    """Update the configuration with JSON input"""
    json_data = json.loads(json_str)
    return Config(**json_data)


def parse_dot_notation_args(dot_notation_args: list) -> dict:
    """Parse dot notation arguments into a nested dictionary"""
    result = {}
    for arg in dot_notation_args:
        key, value = arg.split(":", 1)
        keys = key.split(".")
        d = result
        for k in keys[:-1]:
            if k not in d:
                d[k] = {}
            d = d[k]
        d[keys[-1]] = value.strip()
    return result


def print_schema(model: BaseModel):
    """Print the schema of a Pydantic model"""
    schema = model.schema()
    print(json.dumps(schema, indent=2))


# FastAPI Application with Configuration
app = FastAPI(title="Configurable API")

# Global configuration instance
api_config = APIConfig(
    domain="examples.com",
    email="admin@examples.com",
    container=ContainerConfig(
        host=HostConfig(
            hostname="dev-server", ip_address="192.168.1.100", cpu_cores=4, memory_gb=16
        )
    ),
)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")


@app.get("/config")
async def get_configuration():
    """
    Retrieve the current API configuration

    Returns the complete configuration object
    """
    return api_config


@app.patch("/config")
async def update_configuration(new_config: dict):
    """
    Update the API configuration

    Allows partial or full configuration updates
    """
    global api_config
    try:
        api_config = merge_config(api_config, new_config)
        return {"status": "Configuration updated", "config": api_config}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
