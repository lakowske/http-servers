"""
This module provides an API for recieving emails over imap.
"""

import imaplib

# Replace with your ProtonMail Bridge credentials and server settings
IMAP_SERVER = "127.0.0.1"  # ProtonMail Bridge IMAP server (localhost)
IMAP_PORT = 1143  # Replace with the port given by Bridge
USERNAME = "lakowske@protonmail.com"
PASSWORD = ""

try:
    # Connect to the IMAP server
    mail = imaplib.IMAP4(IMAP_SERVER, IMAP_PORT)
    mail.login(USERNAME, PASSWORD)

    # Select the mailbox you want to access
    mail.select("inbox")

    # Search for all emails
    result, data = mail.search(None, "ALL")
    email_ids = data[0].split()

    print(f"Total emails: {len(email_ids)}")

    # Fetch the latest email and store them to the filesystem
    if email_ids:
        latest_email_id = email_ids[-1]
        result, data = mail.fetch(latest_email_id, "(RFC822)")
        raw_email = data[0][1]
        # Save the email to a file
        with open("latest_email.eml", "wb") as f:
            f.write(raw_email)
        # print(raw_email.decode("utf-8"))  # Print raw email content
except Exception as e:
    print(f"Failed to fetch email: {e}")
