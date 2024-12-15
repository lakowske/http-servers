"""
API for retrieving and updating the configuration object
"""

import logging
from fastapi import APIRouter, HTTPException
from configuration.app import Config
from services.config_service import ConfigService, merge_config
from web.fastapi_provider import RouteProvider

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfigAPI(RouteProvider):
    """
    API for retrieving and updating the configuration object
    """

    def __init__(self, config_service: ConfigService):
        self.config = config_service.config
        self.config_router = APIRouter()

        # Register routes
        self.config_router.add_api_route(
            "/config", self.get_configuration, methods=["GET"]
        )
        self.config_router.add_api_route(
            "/config", self.update_configuration, methods=["PATCH"]
        )

    def get_routes(self):
        """
        Returns the routes for the FastAPI application
        """
        return self.config_router

    async def get_configuration(self) -> Config:
        """
        Retrieve the current API configuration

        Returns the complete configuration object
        """
        return self.config

    async def update_configuration(self, new_config: dict) -> Config | None:
        """
        Update the API configuration

        Allows partial or full configuration updates
        """
        logger.info("Updating configuration with: %s", new_config)
        try:
            updated_config = merge_config(self.config, new_config)
            return updated_config
        except Exception as e:
            logger.error("Error updating configuration: %s", e)
            raise HTTPException(status_code=400, detail=str(e)) from e
