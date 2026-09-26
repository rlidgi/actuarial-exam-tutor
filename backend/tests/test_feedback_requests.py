import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.models.user import User
from app.services import email_service, feedback_request_service

SEND = "app.services.feedback_request_service.email_service.send_feedback_request_email"
CRON_URL = "/api/emails/feedback-requests/send"


@pytest.fixture(autouse=True)
def _no_sleep():
    with patch("app.services.feedback_request_service.time.sleep"):
        yield


def _user(db, email, days_ago, **fields):
    user = User(
        external_auth_id=str(uuid.uuid4()),
        email=email,
        created_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
        **fields,
    )
    db.session.add(user)
    db.session.commit()
    return user


def test_only_users_a_week_old_unsent_and_subscribed_are_due(app, db):
    due = _user(db, "due@example.com", 8)
    _user(db, "new@example.com", 3)
    _user(db, "sent@example.com", 30, feedback_request_sent_at=datetime.now(timezone.utc))
    _user(db, "optout@example.com", 30, email_opt_out=True)

    with patch(SEND, return_value=True) as send:
        result = feedback_request_service.send_due()

    assert [c.args[0].email for c in send.call_args_list] == ["due@example.com"]
    assert result == {"dry_run": False, "due": 1, "sent": 1, "failed": 0, "remaining": 0}
    assert db.session.get(User, due.id).feedback_request_sent_at is not None


def test_failed_send_is_not_marked_and_stays_due(app, db):
    user = _user(db, "fails@example.com", 10)

    with patch(SEND, return_value=False):
        result = feedback_request_service.send_due()

    assert result["sent"] == 0 and result["failed"] == 1 and result["remaining"] == 1
    assert db.session.get(User, user.id).feedback_request_sent_at is None


def test_batches_respect_limit(app, db):
    for i in range(5):
        _user(db, f"u{i}@example.com", 9)

    with patch(SEND, return_value=True) as send:
        first = feedback_request_service.send_due(limit=2)
        second = feedback_request_service.send_due(limit=10)

    assert first["sent"] == 2 and first["remaining"] == 3
    assert second["sent"] == 3 and second["remaining"] == 0
    assert send.call_count == 5


def test_dry_run_sends_nothing(app, db):
    _user(db, "a@example.com", 9)
    _user(db, "b@example.com", 9)

    with patch(SEND) as send:
        result = feedback_request_service.send_due(dry_run=True)

    send.assert_not_called()
    assert result["due"] == 2 and result["sent"] == 0


def test_unsubscribe_links_passed_to_email(app, db):
    app.config["FRONTEND_URL"] = "https://site.example"
    app.config["BACKEND_URL"] = "https://api.example/"
    user = _user(db, "links@example.com", 9)

    with patch(SEND, return_value=True) as send:
        feedback_request_service.send_due()

    token = feedback_request_service.unsubscribe_token(user)
    kwargs = send.call_args.kwargs
    assert kwargs["unsubscribe_url"] == f"https://site.example/unsubscribe?token={token}"
    assert kwargs["one_click_unsubscribe_url"] == f"https://api.example/api/emails/unsubscribe?token={token}"


def test_unsubscribe_endpoint_opts_user_out(client, app, db):
    user = _user(db, "bye@example.com", 9)
    token = feedback_request_service.unsubscribe_token(user)

    resp = client.post("/api/emails/unsubscribe", json={"token": token})
    assert resp.status_code == 200
    assert db.session.get(User, user.id).email_opt_out is True

    # RFC 8058 one-click form: token in the query string, form body
    resp = client.post(
        f"/api/emails/unsubscribe?token={token}", data={"List-Unsubscribe": "One-Click"}
    )
    assert resp.status_code == 200


def test_unsubscribe_rejects_tampered_token(client, app, db):
    user = _user(db, "keep@example.com", 9)
    token = feedback_request_service.unsubscribe_token(user) + "x"

    assert client.post("/api/emails/unsubscribe", json={"token": token}).status_code == 400
    assert client.post("/api/emails/unsubscribe", json={}).status_code == 400
    assert db.session.get(User, user.id).email_opt_out is False


def test_cron_endpoint_requires_secret(client, app, db):
    app.config["CRON_SECRET"] = ""
    assert client.post(CRON_URL, headers={"X-Cron-Secret": ""}).status_code == 403

    app.config["CRON_SECRET"] = "s3cret"
    assert client.post(CRON_URL).status_code == 403
    assert client.post(CRON_URL, headers={"X-Cron-Secret": "wrong"}).status_code == 403


def test_cron_endpoint_runs_batch(client, app, db):
    app.config["CRON_SECRET"] = "s3cret"
    _user(db, "cron@example.com", 9)
    headers = {"X-Cron-Secret": "s3cret"}

    with patch(SEND, return_value=True) as send:
        dry = client.post(CRON_URL, headers=headers, json={"dry_run": True})
        real = client.post(CRON_URL, headers=headers, json={"limit": 5})
        bad = client.post(CRON_URL, headers=headers, json={"limit": 500})

    assert dry.get_json()["due"] == 1
    assert real.get_json()["sent"] == 1
    assert bad.status_code == 400
    assert send.call_count == 1


def test_email_content_and_headers(app, db):
    app.config.update(
        SMTP_PASSWORD="x", SMTP_USERNAME="admin@actuarialexamstutor.com",
        FRONTEND_URL="https://site.example",
    )
    user = _user(db, "reader@example.com", 9)
    server = MagicMock()
    with patch("app.services.email_service.smtplib") as smtplib:
        smtplib.SMTP.return_value.__enter__.return_value = server
        ok = email_service.send_feedback_request_email(
            user, "https://site.example/unsubscribe?token=t", "https://api.example/u?token=t"
        )

    assert ok is True
    msg = server.send_message.call_args.args[0]
    assert msg["To"] == "reader@example.com"
    assert msg["List-Unsubscribe-Post"] == "List-Unsubscribe=One-Click"
    assert "<https://api.example/u?token=t>" in msg["List-Unsubscribe"]
    html = msg.get_body(preferencelist=("html",)).get_content()
    assert "https://site.example/feedback" in html
    assert "https://site.example/unsubscribe?token=t" in html
    assert "Thanks for registering on our platform." in html
    assert "Hi there," in html


def test_email_reports_failure(app, db):
    app.config["SMTP_PASSWORD"] = "x"
    user = _user(db, "down@example.com", 9)
    with patch("app.services.email_service.smtplib") as smtplib:
        smtplib.SMTP.side_effect = OSError("down")
        assert email_service.send_feedback_request_email(user, "u", None) is False

    app.config["SMTP_PASSWORD"] = ""
    assert email_service.send_feedback_request_email(user, "u", None) is False
