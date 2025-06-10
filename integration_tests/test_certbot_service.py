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
        config_service.config.admin.domain,
        staging=False,
        dry_run=False,
    )
    assert success is True


def test_update_apache_configs_to_letsencrypt():
    """
    Test that the certbot service can update Apache configurations to use the
    new certificate.
    """
    certbot = container.certbot_service()
    success = certbot.update_apache_configs_to_letsencrypt(config_service.config.admin.domain)
    assert success


def test_update_dovecot_configs_to_letsencrypt():
    """
    Test that the certbot service can update Dovecot configurations to use the
    new certificate.
    """
    certbot = container.certbot_service()
    success = certbot.update_dovecot_configs_to_letsencrypt(config_service.config.admin.domain)
    assert success


def test_update_postfix_configs_to_letsencrypt():
    """
    Test that the certbot service can update Postfix configurations to use the
    new certificate.
    """
    certbot = container.certbot_service()
    success = certbot.update_postfix_configs_to_letsencrypt(config_service.config.admin.domain)
    assert success
