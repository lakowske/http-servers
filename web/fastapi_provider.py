"""
A simple FastAPI application that allows for the retrieval and updating of a configuration object.
The configuration object is stored in a global container and is updated using a patch request. 
The configuration object is loaded from a YAML file on startup.
"""

from typing import List
from fastapi import FastAPI


class RouteProvider:
    """
    Base class for route providers
    """

    def get_routes(self):
        """
        Returns the routes for the FastAPI application
        """


class AppProvider:
    """
    Base class for application providers
    """

    def __init__(self, route_providers: List[RouteProvider] = None):
        if route_providers is None:
            route_providers = []
        self.route_providers = route_providers
        self.app = None

    def get_app(self):
        """
        Returns the FastAPI application
        """
        if self.app is None:
            self.app = self.create_app()

        return self.app

    def create_app(self):
        """
        Creates the FastAPI application
        """
        app = FastAPI(title="Configurable API")

        for route_provider in self.route_providers:
            app.include_router(route_provider().get_routes())

        return app
