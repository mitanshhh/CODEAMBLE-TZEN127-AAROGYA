from app.api.routes import phc_routes
from app.models.user import User, UserRole
from app.services.email_service import EmailDeliveryResult
from app.services import email_service


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def phc_payload(email: str = "newadmin@example.com"):
    return {
        "name": "Mail Test PHC",
        "type": "PHC",
        "district": "Jalna",
        "state": "Maharashtra",
        "phc_id": "MAIL_TEST_PHC",
        "admin_email": email,
        "admin_mobile": "9999999999",
        "location": "Jalna",
        "health_score": 100,
        "status": "Active",
    }


def test_create_phc_returns_email_sent_status(client, admin_token, db_session, monkeypatch):
    def fake_send_onboarding_email(*args, **kwargs):
        return EmailDeliveryResult(sent=True, detail="Onboarding email sent.")

    monkeypatch.setattr(phc_routes, "send_onboarding_email", fake_send_onboarding_email)

    response = client.post("/api/v1/phc/", json=phc_payload(), headers=auth(admin_token))

    assert response.status_code == 200
    body = response.json()
    assert body["admin_user_created"] is True
    assert body["email_sent"] is True
    assert body["email_detail"] == "Onboarding email sent."
    user = db_session.query(User).filter(User.email == "newadmin@example.com").first()
    assert user is not None
    assert user.role == UserRole.MEDICAL_OFFICER


def test_create_phc_reports_email_failure_without_creating_unusable_admin(client, admin_token, db_session, monkeypatch):
    def fake_send_onboarding_email(*args, **kwargs):
        return EmailDeliveryResult(sent=False, detail="SMTP authentication failed.")

    monkeypatch.setattr(phc_routes, "send_onboarding_email", fake_send_onboarding_email)

    response = client.post("/api/v1/phc/", json=phc_payload("failadmin@example.com"), headers=auth(admin_token))

    assert response.status_code == 200
    body = response.json()
    assert body["admin_user_created"] is False
    assert body["email_sent"] is False
    assert body["email_detail"] == "SMTP authentication failed."
    user = db_session.query(User).filter(User.email == "failadmin@example.com").first()
    assert user is None


def test_email_service_reports_tls_verification_hint(monkeypatch):
    class FakeSMTP:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def starttls(self, context=None):
            import ssl

            raise ssl.SSLError("certificate verify failed")

        def login(self, *args, **kwargs):
            pass

        def send_message(self, *args, **kwargs):
            pass

    monkeypatch.setenv("SMTP_EMAIL", "sender@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "password")
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USE_TLS", "true")
    monkeypatch.setattr(email_service.smtplib, "SMTP", FakeSMTP)

    result = email_service.send_onboarding_email("to@example.com", "to@example.com", "generated-password")

    assert result.sent is False
    assert "SMTP_SSL_VERIFY=false" in result.detail
