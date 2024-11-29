"""
A service to provide email functionality.
"""

from mail.imap import fetch_email, fetch_first
from mail.smtp import send_email
from configuration.app import ImapConfig, SmtpConfig


class MailService:
    """
    Mail service interacts with an imap server and smtp server to send and receive emails.
    """

    def __init__(self, imap: ImapConfig, smtp: SmtpConfig):
        self.imap = imap
        self.smtp = smtp

    def fetch_email(self):
        """
        Fetch email from the imap server.
        """
        return fetch_email(
            self.imap.server,
            self.imap.port,
            self.imap.username,
            self.imap.password,
        )

    def fetch_first_email(self):
        """
        Fetch the first email from the imap server.
        """
        return fetch_first(
            self.imap.server,
            self.imap.port,
            self.imap.username,
            self.imap.password,
        )

    def send_email(self, to: str, subject: str, body: str):
        """
        Send an email using the smtp server.
        """
        return send_email(
            self.smtp.username,
            self.smtp.password,
            self.smtp.sender_email,
            to,
            subject,
            body,
            self.smtp.server,
            self.smtp.port,
        )
