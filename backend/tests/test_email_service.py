import uuid
from unittest.mock import MagicMock, patch

from app.models.user import User
from app.services import email_service


def _make_user(db, email):
    user = User(external_auth_id=str(uuid.uuid4()), email=email)
    db.session.add(user)
    db.session.commit()
    return user


def test_send_welcome_email_noops_when_smtp_not_configured(app, db):
    user = _make_user(db, "nosmtp@example.com")
    app.config["SMTP_PASSWORD"] = ""

    with patch("app.services.email_service.smtplib") as mock_smtplib:
        email_service.send_welcome_email(user)

    mock_smtplib.SMTP.assert_not_called()


def test_send_welcome_email_sends_via_smtp_when_configured(app, db):
    user = _make_user(db, "withsmtp@example.com")
    app.config["SMTP_PASSWORD"] = "hunter2"
    app.config["SMTP_USERNAME"] = "admin@actuarialexamstutor.com"
    app.config["SMTP_HOST"] = "mail.privateemail.com"
    app.config["SMTP_PORT"] = 587

    mock_server = MagicMock()
    with patch("app.services.email_service.smtplib") as mock_smtplib:
        mock_smtplib.SMTP.return_value.__enter__.return_value = mock_server
        email_service.send_welcome_email(user)

    mock_smtplib.SMTP.assert_called_once_with("mail.privateemail.com", 587)
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with("admin@actuarialexamstutor.com", "hunter2")
    mock_server.send_message.assert_called_once()
    sent_message = mock_server.send_message.call_args.args[0]
    assert sent_message["To"] == "withsmtp@example.com"
    assert sent_message["From"] == "admin@actuarialexamstutor.com"
    assert "Welcome to Actuarial Exams Tutor" in sent_message["Subject"]
    plain_body = sent_message.get_body(preferencelist=("plain",)).get_content()
    assert user.referral_code in plain_body


def test_send_welcome_email_swallows_smtp_errors(app, db):
    user = _make_user(db, "smtpfails@example.com")
    app.config["SMTP_PASSWORD"] = "hunter2"

    with patch("app.services.email_service.smtplib") as mock_smtplib:
        mock_smtplib.SMTP.side_effect = OSError("connection refused")
        email_service.send_welcome_email(user)  # must not raise
