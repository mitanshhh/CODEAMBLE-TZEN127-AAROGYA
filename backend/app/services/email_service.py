import os
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path
from typing import Optional

try:
    from dotenv import dotenv_values
except Exception:  # pragma: no cover
    dotenv_values = None


@dataclass
class EmailDeliveryResult:
    sent: bool
    detail: str


def _env_value(name: str, default: str = "") -> str:
    if name in os.environ:
        return os.environ[name]
    if dotenv_values:
        root_env = dotenv_values(".env")
        if root_env.get(name) is not None:
            return str(root_env[name])
        backend_env = Path(__file__).resolve().parents[2] / ".env"
        backend_values = dotenv_values(backend_env)
        if backend_values.get(name) is not None:
            return str(backend_values[name])
    return default


def _env_bool(name: str, default: bool = True) -> bool:
    value = _env_value(name, str(default)).strip().lower()
    return value not in {"0", "false", "no", "off"}


def _env_int(name: str, default: int) -> int:
    try:
        return int(_env_value(name, str(default)))
    except ValueError:
        return default


def _from_header(email_address: str) -> str:
    from_name = _env_value("SMTP_FROM_NAME", "Aarogya Health Engine").strip()
    return f"{from_name} <{email_address}>" if from_name else email_address


def _ssl_context():
    if _env_bool("SMTP_SSL_VERIFY", True):
        return ssl.create_default_context()
    return ssl._create_unverified_context()


def send_onboarding_email(
    email_to: str,
    username: str,
    raw_password: str,
    centre_name: Optional[str] = None,
) -> EmailDeliveryResult:
    smtp_user = _env_value("SMTP_EMAIL").strip()
    smtp_password = _env_value("SMTP_PASSWORD").strip()
    smtp_host = _env_value("SMTP_HOST", "smtp.gmail.com").strip()
    smtp_port = _env_int("SMTP_PORT", 587)
    smtp_use_ssl = _env_bool("SMTP_USE_SSL", smtp_port == 465)
    smtp_use_tls = _env_bool("SMTP_USE_TLS", not smtp_use_ssl)
    ssl_context = _ssl_context()

    if not smtp_user or not smtp_password:
        return EmailDeliveryResult(
            sent=False,
            detail="SMTP_EMAIL and SMTP_PASSWORD are not configured in the backend environment.",
        )

    msg = EmailMessage()
    msg["Subject"] = f"Welcome to Aarogya Health Engine{f' - {centre_name}' if centre_name else ''}"
    msg["From"] = _from_header(smtp_user)
    msg["To"] = email_to
    msg.set_content(
        f"""Hello,

Your health centre{f" '{centre_name}'" if centre_name else ""} has been registered on Aarogya Health Engine.

You can log in using:
Username: {username}
Email: {email_to}
Password: {raw_password}

Please change your password immediately after logging in.

Regards,
Aarogya District Administration
"""
    )

    try:
        if smtp_use_ssl:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=20, context=ssl_context) as smtp:
                smtp.login(smtp_user, smtp_password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as smtp:
                if smtp_use_tls:
                    smtp.starttls(context=ssl_context)
                smtp.login(smtp_user, smtp_password)
                smtp.send_message(msg)
    except smtplib.SMTPAuthenticationError:
        return EmailDeliveryResult(
            sent=False,
            detail="SMTP authentication failed. Check SMTP_EMAIL and SMTP_PASSWORD/app password.",
        )
    except ssl.SSLError as exc:
        return EmailDeliveryResult(
            sent=False,
            detail=f"SMTP TLS certificate verification failed: {exc}. For local development only, set SMTP_SSL_VERIFY=false.",
        )
    except Exception as exc:
        return EmailDeliveryResult(sent=False, detail=f"SMTP delivery failed: {exc}")

    return EmailDeliveryResult(sent=True, detail="Onboarding email sent.")
