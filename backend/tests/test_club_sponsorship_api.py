from unittest.mock import patch

import pytest

from app.api import contact

URL = "/api/contact/club-sponsorship"
FIELDS = {
    "name": "Sam Treasurer",
    "email": "sam@psu.edu",
    "university": "Penn State",
    "event_dates": "Oct 14 general meeting",
}
VALID = {**FIELDS, "human_check": "3"}
SEND = "app.api.contact.email_service.send_club_sponsorship_email"


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    contact._recent_submissions.clear()
    yield
    contact._recent_submissions.clear()


def test_valid_request_sends_email(client):
    with patch(SEND) as send:
        resp = client.post(URL, json=VALID)

    assert resp.status_code == 200
    send.assert_called_once_with(**FIELDS)


@pytest.mark.parametrize("answer", ["3", " 3 ", "three", "Three"])
def test_accepted_human_check_answers(client, answer):
    with patch(SEND) as send:
        resp = client.post(URL, json={**VALID, "human_check": answer})

    assert resp.status_code == 200
    send.assert_called_once()


@pytest.mark.parametrize("answer", ["", "4", "12"])
def test_wrong_human_check_rejected(client, answer):
    with patch(SEND) as send:
        resp = client.post(URL, json={**VALID, "human_check": answer})

    assert resp.status_code == 400
    send.assert_not_called()


@pytest.mark.parametrize("missing", ["name", "email", "university", "event_dates"])
def test_required_fields(client, missing):
    with patch(SEND) as send:
        resp = client.post(URL, json={**VALID, missing: " "})

    assert resp.status_code == 400
    send.assert_not_called()


def test_rejects_bad_email(client):
    with patch(SEND) as send:
        assert client.post(URL, json={**VALID, "email": "nope"}).status_code == 400
    send.assert_not_called()


def test_honeypot_silently_accepts_without_sending(client):
    with patch(SEND) as send:
        resp = client.post(URL, json={**VALID, "website": "spam.example"})

    assert resp.status_code == 200
    send.assert_not_called()


def test_rate_limit_shared_with_other_forms(client):
    with patch(SEND), patch("app.api.contact.email_service.send_contact_email"):
        for _ in range(5):
            client.post("/api/contact", json={"name": "a", "email": "a@b.co", "message": "hi"})
        resp = client.post(URL, json=VALID)

    assert resp.status_code == 429


def test_email_body(app):
    app.config["SMTP_PASSWORD"] = "x"
    from app.services import email_service

    with patch("app.services.email_service._send_admin_notification") as notify:
        email_service.send_club_sponsorship_email(**FIELDS)

    kwargs = notify.call_args.kwargs
    assert kwargs["subject"] == "Actuarial Club sponsorship request: Penn State"
    assert kwargs["reply_to"] == "sam@psu.edu"
    assert "Upcoming meeting/event date(s): Oct 14 general meeting" in kwargs["body"]
