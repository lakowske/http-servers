"""
A simple FastAPI application that allows for the retrieval and updating of a configuration object. The configuration object is stored in a global container and is updated using a patch request. The configuration object is loaded from a YAML file on startup.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.websockets import (
    WebSocketState,
    WebSocket,
    WebSocketDisconnect,
)
from configuration.container import ServerContainer
from configuration.app import Config
from services.config_service import merge_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

connected_websockets = set()


@asynccontextmanager
async def lifespan(app: FastAPI, websockets: set = connected_websockets):
    """
    Context manager to handle the lifespan of the FastAPI application.
    """
    print("We starting up")
    yield
    print("Shutting down websockets")
    for websocket in connected_websockets:
        print("Attempting to close websocket %s" % str(websocket.client))
        if not websocket.client_state.name != WebSocketState.DISCONNECTED:
            await websocket.close()


# FastAPI Application with Configuration
app = FastAPI(
    title="Configurable API",
    description="API with configuration management",
    version="0.1.0",
    lifespan=lifespan,
)

# Global configuration instance
container = ServerContainer()
config_service = container.config_service()
config_service.load_yaml_config("secrets/config.yaml")
api_config = config_service.config


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for retrieving and updating configuration.
    """
    await websocket.accept()
    connected_websockets.add(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect as e:
        logger.info("Got a disconnect exception: %s", e)
        return
    except RuntimeError as e:
        logger.error("Error processing websocket: %s", e)
        connected_websockets.remove(websocket)
        if not websocket.client_state != WebSocketState.DISCONNECTED:
            try:
                await websocket.close()
            except RuntimeError as e:
                logger.error("Error closing websocket: %s", e)


@app.get("/config")
async def get_configuration():
    """
    Retrieve the current API configuration

    Returns the complete configuration object
    """
    return api_config


@app.patch("/config")
async def update_configuration(new_config: dict, config: Config = api_config):
    """
    Update the API configuration

    Allows partial or full configuration updates
    """
    logger.info("Updating configuration with: %s", new_config)
    try:
        updated_config = merge_config(config, new_config)
        return {"status": "Configuration updated", "config": updated_config}
    except (ValueError, TypeError) as e:
        logger.error("Error updating configuration: %s", e)
        raise HTTPException(status_code=400, detail=str(e)) from e
