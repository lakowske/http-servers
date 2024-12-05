"""
A service to interact with letsencrypt's certbot client.  Performs common operations so that
the user does not have to manage configuration or run certbot commands directly.
"""

import logging

from configuration.app import WORKSPACE
from auth.certificates import certbot_ssl, update_apache_ssl_config_to_letsencrypt
from services.config_service import ConfigService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CertbotService:
    """
    A service to interact with letsencrypt's certbot client.  Performs common operations so that
    the user does not have to manage configuration or run certbot commands directly.
    """

    def __init__(self, config_service: ConfigService):
        self.config = config_service.config
        self.web_root_path = self.config.build_paths.get("webroot").tree_root_path(
            WORKSPACE
        )
        self.certbot_config_path = (
            self.config.build_paths.get("apache")
            .get("conf")
            .get("letsencrypt")
            .tree_root_path(WORKSPACE)
        )
        self.certbot_work_path = (
            self.config.build_paths.get("certbot").get("work").tree_root_path(WORKSPACE)
        )
        self.certbot_logs_path = (
            self.config.build_paths.get("certbot").get("logs").tree_root_path(WORKSPACE)
        )
        if self.config.runtime.withinContainer:
            self.certbot_ssl_config_path = (
                self.config.container_paths.get("conf")
                .get("extra")
                .get("httpd-ssl.conf")
                .tree_root_path("")
            )
        else:
            self.certbot_ssl_config_path = (
                self.config.build_paths.get("apache")
                .get("conf")
                .get("extra")
                .get("httpd-ssl.conf")
                .tree_root_path(WORKSPACE)
            )
        self.email = self.config.admin.email

    def create_certificate(
        self, domain: str, staging: bool = True, dry_run: bool = True
    ) -> bool:
        """
        Create a certificate for the given domain using certbot.
        """
        logger.info("Creating certificate for domain: %s", domain)
        certbot_ssl(
            self.web_root_path,
            self.certbot_config_path,
            self.certbot_work_path,
            self.certbot_logs_path,
            self.certbot_ssl_config_path,
            [domain],
            self.email,
            staging=staging,
            dry_run=dry_run,
        )
        logger.info("Certificate created for domain: %s", domain)
        return True

    def update_apache_configs_to_letsencrypt(self, domain: str) -> None:
        """
        Update the Apache configuration to use the new certificate.
        """
        logger.info("Updating Apache configuration for domain: %s", domain)
        update_apache_ssl_config_to_letsencrypt(self.certbot_ssl_config_path, [domain])
        logger.info("Apache configuration updated for domain: %s", domain)
        return True
