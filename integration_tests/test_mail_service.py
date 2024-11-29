"""
This module contains the integration tests for the mail_service module.  A set of
valid email services are required to run these tests.  Ensure that an imap and smtp
server are running and that the configuration is correct.
"""

from configuration.container import ServerContainer


def test_imap_inbox_recieve():
    """
    Test that the mail service can fetch emails from an imap server.
    """
    container = ServerContainer()
    config_service = container.config_service()
    config_service.load_yaml_config("email-secrets.yaml")

    mail_service = container.mail_service()

    inbox = mail_service.fetch_first_email()
    assert inbox is not None
    assert len(inbox) == 1
