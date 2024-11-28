"""
This module provides a function to send an email using the SMTP server.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email(
    username: str,
    password: str,
    sender_email: str,
    receiver_email: str,
    subject: str,
    body: str,
    smtp_server: str = "127.0.0.1",
    smtp_port: int = 1025,
):
    """
    Send an email using the SMTP server.
    """

    # Create the email message
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    # Send the email
    try:
        # Enable debugging output
        smtp = smtplib.SMTP(smtp_server, smtp_port)
        smtp.set_debuglevel(1)

        # Start TLS if needed
        smtp.starttls()

        # Login and send email
        smtp.login(username, password)
        smtp.sendmail(sender_email, receiver_email, msg.as_string())
        smtp.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")
