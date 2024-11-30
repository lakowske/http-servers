"""
This module provides an API for recieving emails over imap.
"""

from typing import List, Tuple, Optional
import logging
import imaplib
import email
import time
from email.header import decode_header

from configuration.app import ImapConfig
from mail.smtp import Email

IMAP_ERROR_MSG = "IMAP error: %s"
RFC822_LITERAL = "(RFC822)"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_raw_email(raw_email: bytes) -> Email:
    """
    Parse a raw email into an Email object.
    """
    msg = email.message_from_bytes(raw_email)

    # Decode the email subject
    subject, encoding = decode_header(msg["Subject"])[0]
    if isinstance(subject, bytes):
        subject = subject.decode(encoding if encoding else "utf-8")

    # Get the email body
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            if "attachment" not in content_disposition:
                if content_type == "text/plain" or content_type == "text/html":
                    body = part.get_payload(decode=True).decode()
    else:
        body = msg.get_payload(decode=True).decode()

    mail = Email(
        to=msg.get("To"),
        from_=msg.get("From"),
        date=msg.get("Date"),
        subject=subject,
        body=body,
    )
    return mail


class ImapService:
    """
    A service to interact with an IMAP server.  Performs common operations so that
    the user does not have to interact with IMAP directly.
    """

    def __init__(self, imap_config: ImapConfig, mailbox: str = "inbox"):
        self.config = imap_config
        self.mailbox = mailbox
        # We login right away so that we can use the mail object for all operations
        # without having to login each time.  The assumption is that the user wants
        # a simple interface to the IMAP server, otherwise they would use the IMAP
        # library directly.
        self.login()
        self.mail.select(mailbox)

    def login(self) -> Tuple[Optional[Exception], Optional[imaplib.IMAP4]]:
        """
        Login to the IMAP server.
        """
        try:
            # Connect to the IMAP server
            mail = imaplib.IMAP4(self.config.server, self.config.port)
            mail.login(self.config.username, self.config.password)
            self.mail = mail
            return None, mail
        except imaplib.IMAP4.error as e:
            logger.error(IMAP_ERROR_MSG, e)
            return e, None

    def search(
        self, search_criteria: str
    ) -> Tuple[Optional[Exception], Optional[List[str]]]:
        """
        Search the IMAP server for emails.
        """
        try:
            # Search for all emails
            result, data = self.mail.search(None, search_criteria)
            if result != "OK":
                logger.error("Failed to fetch emails: %s", result)
                return Exception(f"Failed to fetch emails: {result}"), None

            email_ids = data[0].split()
            return None, email_ids
        except imaplib.IMAP4.error as e:
            logger.error(IMAP_ERROR_MSG, e)
            return e, None

    def fetch_email(self, email_id: str) -> Tuple[Optional[Exception], Optional[Email]]:
        """
        Fetch an email from the IMAP server.
        """
        try:
            # Fetch the email by ID
            result, data = self.mail.fetch(email_id, RFC822_LITERAL)
            if result != "OK":
                logger.error("Failed to fetch email: %s", result)
                return Exception(f"Failed to fetch email: {result}"), None

            raw_email = data[0][1]
            return None, parse_raw_email(raw_email)
        except imaplib.IMAP4.error as e:
            logger.error("IMAP error: %s", e)
            return e, None

    def delete_email(self, email_id: str) -> Optional[Exception]:
        """
        Delete an email from the IMAP server.
        """
        try:
            # Mark the email for deletion
            result = self.mail.store(email_id, "+FLAGS", "\\Deleted")
            if result[0] != "OK":
                logger.error("Failed to mark email for deletion: %s", result)
                return Exception(f"Failed to mark email for deletion: {result}")

            # Permanently remove all emails marked for deletion
            result = self.mail.expunge()
            if result[0] != "OK":
                logger.error("Failed to expunge emails: %s", result)
                return Exception(f"Failed to expunge emails: {result}")

            return None
        except imaplib.IMAP4.error as e:
            logger.error("IMAP error: %s", e)
            return e

    def inbox_size(self) -> Tuple[Optional[Exception], Optional[int]]:
        """
        Get the size of the inbox.
        """
        e, email_ids = self.fetch_all_mail_ids()
        if e is None and email_ids is not None:
            return None, len(email_ids)
        return e, None

    def fetch_all_mail_ids(self) -> Tuple[Optional[Exception], Optional[List[str]]]:
        """
        Fetch the inbox email ids from the IMAP server.
        """
        return self.search("ALL")

    def fetch_all(self) -> Tuple[Optional[Exception], Optional[List[Email]]]:
        """
        Fetch all emails from the IMAP server.
        """
        e, email_ids = self.fetch_all_mail_ids()
        if e is not None:
            return e, None

        emails = []
        for email_id in email_ids:
            e, mail = self.fetch_email(email_id)
            if e is not None:
                return e, None
            emails.append(mail)
        return None, emails

    def fetch_from(
        self, from_email_address: str
    ) -> Tuple[Optional[Exception], Optional[List[Email]]]:
        """
        Fetch the first email from the IMAP server.
        """
        e, email_ids = self.search(f'(FROM "{from_email_address}")')
        if e is None and email_ids is not None:
            emails = []
            for email_id in email_ids:
                e, mail = self.fetch_email(email_id)
                if e is not None:
                    return e, None
                emails.append(mail)
            return None, emails

        return e, None

    def poll(self, closure, interval=1, timeout=30):
        """
        Poll the IMAP server until the closure returns a non-None value.
        """
        while True:
            result = closure(self)
            if result:
                return result
            time.sleep(interval)
            timeout -= interval
            if timeout <= 0:
                return None
