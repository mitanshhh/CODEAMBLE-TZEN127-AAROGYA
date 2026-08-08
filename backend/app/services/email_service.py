import smtplib
from email.message import EmailMessage
from app.core.config import settings

def send_onboarding_email(email_to: str, username: str, raw_password: str):
    if not settings.SMTP_EMAIL or not settings.SMTP_PASSWORD:
        print(f"Mock Email sent to {email_to} (SMTP not configured). Password: {raw_password}")
        return

    msg = EmailMessage()
    msg['Subject'] = 'Welcome to Aarogya Health Engine'
    msg['From'] = settings.SMTP_EMAIL
    msg['To'] = email_to

    content = f"""
    Welcome {username},
    
    Your account for the Aarogya Health Engine has been created.
    Please use the following credentials to log in:
    Username: {username}
    Password: {raw_password}
    
    Please change your password upon logging in.
    """
    msg.set_content(content)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(settings.SMTP_EMAIL, settings.SMTP_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")
