"""
This module contains the integration tests for the mail_service module.  A set of
valid email services are required to run these tests.  Ensure that an imap and smtp
server are running and that the configuration is correct.
"""

import uuid
from configuration.container import ServerContainer
from mail.smtp import Email


TEST_ADDRESS = "lakowske@protonmail.com"

container = ServerContainer()
config_service = container.config_service()
config_service.load_yaml_config("email-secrets.yaml")


def test_imap_inbox_size():
    """
    Test that the mail service can get the size of the inbox.
    """
    imap = container.imap_service()
    e, size = imap.inbox_size()
    assert e is None
    assert size is not None
    assert size >= 0


def test_imap_fetch_all():
    """
    Test that the mail service can fetch all emails from an imap server.
    """
    imap = container.imap_service()
    e, mail = imap.fetch_all()
    assert e is None
    assert mail is not None
    messages = len(mail)
    assert messages >= 0


def test_smtp_send_email():
    """
    Test that the mail service can send an email using an smtp server.
    """
    smtp = container.smtp_service()

    # Generate a uuid to track the email
    message_uuid = uuid.uuid4()
    mail = Email(
        to=TEST_ADDRESS,
        from_=TEST_ADDRESS,
        subject=f"Test Email {message_uuid}",
        body=f"This is a test email {message_uuid} from the mail service.",
    )

    result = smtp.send_email(mail)
    assert result is True


def test_roundtrip_email():
    """
    Test that the mail service can send and receive an email.
    """
    smtp = container.smtp_service()
    imap = container.imap_service()

    # Generate a uuid to track the email
    message_uuid = uuid.uuid4()
    mail = Email(
        to=TEST_ADDRESS,
        from_=TEST_ADDRESS,
        subject=f"Round Trip Email Test {message_uuid}",
        body=f"This is a test email {message_uuid} from the mail service.",
    )

    result = smtp.send_email(mail)

    assert result is True

    def check_for_email(imap):
        e, mails = imap.fetch_from(TEST_ADDRESS)
        if e is None and mails is not None:
            for some_mail in mails:
                if some_mail.subject == f"Round Trip Email Test {message_uuid}":
                    return some_mail
        return None

    # Wait a while for the email to arrive
    result = imap.poll(check_for_email, interval=1, timeout=30)
    assert result is not None
