"""
FastAPI application with configuration management
"""

from typing import Dict, Any, TypeVar
import json
import logging
from fastapi import FastAPI, HTTPException, WebSocket
from pydantic import BaseModel


from configuration.app import Config
from configuration.tree_nodes import AdminContext
from services.config_service import merge_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

T = TypeVar("T")


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
    admin_context=AdminContext(
        domain="example.com",
        email="admin@example.com",
    )
)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for retrieving and updating configuration
    """
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
