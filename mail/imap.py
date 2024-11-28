"""
This module provides an API for recieving emails over imap.
"""

import imaplib


def fetch_email(
    imap_server: str = "127.0.0.1",
    imap_port: int = 1143,
    username: str = "",
    password: str = "",
):
    """
    Fetch the latest email from the IMAP server.
    """
    try:
        # Connect to the IMAP server
        mail = imaplib.IMAP4(imap_server, imap_port)
        mail.login(username, password)

        # Select the mailbox you want to access
        mail.select("inbox")

        # Search for all emails
        result, data = mail.search(None, "ALL")
        email_ids = data[0].split()

        print(f"Total emails: {len(email_ids)}")

        emails = {}
        # Fetch the latest email and store them in a dictionary
        for email_id in email_ids:
            result, data = mail.fetch(email_id, "(RFC822)")
            raw_email = data[0][1]
            emails[email_id] = raw_email.decode("utf-8")
        return emails
    except Exception as e:
        print(f"Failed to fetch email: {e}")
