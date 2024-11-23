import logging
from fastapi import FastAPI, HTTPException, WebSocket
from pydantic import BaseModel
from typing import List, Dict, Any, TypeVar
import copy
import json
import yaml

from configuration.app import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

T = TypeVar("T")


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
api_config = Config(
    domain="example.com",
    email="admin@example.com",
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
    logger.info(f"Updating configuration with: {new_config}")
    try:
        api_config = merge_config(api_config, new_config)
        return {"status": "Configuration updated", "config": api_config}
    except Exception as e:
        logger.error(f"Error updating configuration: {e}")
        raise HTTPException(status_code=400, detail=str(e))
