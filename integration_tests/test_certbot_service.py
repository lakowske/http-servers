"""
Test the ability to request a certificate from Let's Encrypt using certbot.
"""

from configuration.container import ServerContainer

SECRETS_FILE = "secrets/config.yaml"
container = ServerContainer()
config_service = container.config_service()
config_service.load_yaml_config(SECRETS_FILE)


def test_certbot():
    """
    Test that the certbot service can request a certificate from Let's Encrypt.
    """
    certbot = container.certbot_service()
    success = certbot.create_certificate(
        config_service.config.admin_context.domain, dry_run=False
    )
    assert success is True
