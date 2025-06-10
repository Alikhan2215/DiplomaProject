import smtplib
from email.mime.text import MIMEText
from app.core.config import settings

def send_verification_email(to_email: str, code: str) -> None:
    subject = "Your verification code"
    body = f"Your verification code is: {code}\n\nIt expires in 10 minutes."
    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = settings.mail_username
    message["To"] = to_email

    # Connect via SSL on port settings.mail_port (465)
    with smtplib.SMTP_SSL(settings.mail_host, settings.mail_port) as server:
        server.login(settings.mail_username, settings.mail_password)
        server.sendmail(settings.mail_username, [to_email], message.as_string())
