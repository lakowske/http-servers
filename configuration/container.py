"""
This module provides a services for testing and application use.
"""

from typing import List
from dependency_injector import containers, providers
from fastapi import FastAPI
from configuration.tree_nodes import AdminContext
from configuration.app import PodmanConfig, Config
from configuration.app import ImapConfig
from configuration.app import SmtpConfig
from services.podman_service import PodmanService
from services.config_service import ConfigService
from services.httpd_service import HttpdService
from services.certbot_service import CertbotService
from services.git_service import GitService
from services.user_service import UserService
from web.config_api import ConfigAPI
from web.fastapi_provider import AppProvider, RouteProvider
from mail.imap import ImapService
from mail.smtp import SmtpService


def create_imap_service(config_service: ConfigService) -> ImapService:
    """
    Creates an ImapService object from an AppConfig object.
    """
    return ImapService(config_service.config.imap)


def to_imap_config(config_service: ConfigService) -> ImapConfig:
    """
    Converts a ConfigService object to an ImapConfig object.
    """
    return config_service.config.imap


def to_smtp_config(config_service: ConfigService) -> SmtpConfig:
    """
    Converts a ConfigService object to an SmtpConfig object.
    """
    return config_service.config.smtp


def to_podman_config(config_service: ConfigService) -> PodmanConfig:
    """
    Converts a ConfigService object to an PodmanConfig object.
    """
    return config_service.config.podman


def create_config_service() -> ConfigService:
    """
    Creates a ConfigService object.
    """

    config = Config(
        admin=AdminContext(
            domain="example.com",
            email="admin@example.com",
        )
    )

    return ConfigService(config=config)


def create_openapi_service(routers: List[RouteProvider]) -> FastAPI:
    """
    Creates a FastAPI application with a configuration object
    """
    app = FastAPI(title="Configurable API")

    for router in routers:
        app.include_router(router.get_routes())

    return app


class ServerContainer(containers.DeclarativeContainer):
    """
    Dependency injection container for configuration loading
    """

    config = providers.Configuration()

    config_service = providers.Singleton(create_config_service)

    podman_config = providers.Singleton(to_podman_config, config_service=config_service)

    imap_config = providers.Factory(to_imap_config, config_service=config_service)

    smtp_config = providers.Factory(to_smtp_config, config_service=config_service)

    podman_service = providers.Factory(PodmanService, podman_config=podman_config)

    imap_service = providers.Singleton(ImapService, imap_config=imap_config)

    smtp_service = providers.Singleton(SmtpService, smtp_config=smtp_config)

    httpd_service = providers.Singleton(
        HttpdService, podman_service=podman_service, config_service=config_service
    )

    certbot_service = providers.Singleton(CertbotService, config_service=config_service)

    git_service = providers.Singleton(GitService, config_service=config_service)

    user_service = providers.Singleton(UserService, config_service=config_service)

    config_api = providers.Singleton(ConfigAPI, config_service=config_service)

    app_provider = providers.Singleton(AppProvider, route_providers=[config_api])
