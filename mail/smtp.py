"""
This module provides a function to send an email using the SMTP server.
"""

from typing import Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


from pydantic import BaseModel
from configuration.app import SmtpConfig


class Email(BaseModel):
    """
    An email object.
    """

    to: str
    from_: str
    date: Optional[str] = None
    subject: str
    body: str


class SmtpService:
    """
    A service to interact with an SMTP server.  Performs common operations so that
    the user does not have to interact with SMTP directly.
    """

    def __init__(self, smtp_config: SmtpConfig):
        self.smtp_config = smtp_config
        self.login()

    def login(self):
        """
        Login to the SMTP server.
        """
        smtp = smtplib.SMTP(self.smtp_config.server, self.smtp_config.port)
        smtp.starttls()
        smtp.login(self.smtp_config.username, self.smtp_config.password)
        return smtp

    def send_email(self, email: Email):
        """
        Send an email using the SMTP server.
        """
        # Create the email message
        msg = MIMEMultipart()
        msg["From"] = email.from_
        msg["To"] = email.to
        msg["Subject"] = email.subject
        msg.attach(MIMEText(email.body, "plain"))

        # Send the email
        try:
            # Enable debugging output
            smtp = smtplib.SMTP(self.smtp_config.server, self.smtp_config.port)
            smtp.set_debuglevel(1)

            # Start TLS if needed
            smtp.starttls()

            # Login and send email
            smtp.login(self.smtp_config.username, self.smtp_config.password)
            smtp.sendmail(email.from_, email.to, msg.as_string())
            smtp.quit()
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
