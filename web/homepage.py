"""
A simple FastAPI application that allows for the retrieval and updating of a configuration object. The configuration object is stored in a global container and is updated using a patch request. The configuration object is loaded from a YAML file on startup.
"""

import logging
from fastapi import FastAPI, HTTPException
from configuration.container import ServerContainer
from configuration.app import Config
from services.config_service import merge_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# FastAPI Application with Configuration
app = FastAPI(title="Configurable API")

# Global configuration instance
container = ServerContainer()
config_service = container.config_service()
config_service.load_yaml_config("secrets/config.yaml")
api_config = config_service.config


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
    except Exception as e:
        logger.error("Error updating configuration: %s", e)
        raise HTTPException(status_code=400, detail=str(e)) from e
