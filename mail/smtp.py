import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Replace with your ProtonMail Bridge credentials and server settings
SMTP_SERVER = "127.0.0.1"  # ProtonMail Bridge SMTP server (localhost)
SMTP_PORT = 1025  # Replace with the port given by Bridge
USERNAME = "lakowske@protonmail.com"
PASSWORD = ""

# Email details
sender_email = "lakowske@protonmail.com"
receiver_email = "lakowske@gmail.com"
subject = "Test Email from Python"
body = "This is a test email sent using Python and ProtonMail Bridge."

# Create the email message
msg = MIMEMultipart()
msg["From"] = sender_email
msg["To"] = receiver_email
msg["Subject"] = subject
msg.attach(MIMEText(body, "plain"))

# Send the email
try:
    # Enable debugging output
    smtp = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    smtp.set_debuglevel(1)

    # Start TLS if needed
    smtp.starttls()

    # Login and send email
    smtp.login(USERNAME, PASSWORD)
    smtp.sendmail(sender_email, receiver_email, msg.as_string())
    smtp.quit()
    print("Email sent successfully!")
except Exception as e:
    print(f"Failed to send email: {e}")
