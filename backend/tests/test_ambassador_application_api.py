from unittest.mock import patch

import pytest

from app.api import contact

VALID = {
    "name": "Pat Student",
    "email": "pat@psu.edu",
    "school": "Penn State",
    "graduation_year": "2028",
    "actuarial_club": "yes",
    "exams": "Passed P, studying for FM.",
    "message": "I run the study group.",
}


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    contact._recent_submissions.clear()
    yield
    contact._recent_submissions.clear()


def test_valid_application_sends_email(client):
    with patch("app.api.contact.email_service.send_ambassador_application_email") as send:
        resp = client.post("/api/contact/ambassador", json=VALID)

    assert resp.status_code == 200
    send.assert_called_once_with(**VALID)


def test_optional_fields_may_be_blank(client):
    body = {**VALID, "graduation_year": "", "actuarial_club": ""}
    with patch("app.api.contact.email_service.send_ambassador_application_email") as send:
        resp = client.post("/api/contact/ambassador", json=body)

    assert resp.status_code == 200
    send.assert_called_once()


@pytest.mark.parametrize("missing", ["name", "email", "school", "exams", "message"])
def test_required_fields(client, missing):
    with patch("app.api.contact.email_service.send_ambassador_application_email") as send:
        resp = client.post("/api/contact/ambassador", json={**VALID, missing: "  "})

    assert resp.status_code == 400
    send.assert_not_called()


def test_rejects_bad_email_and_club_answer(client):
    with patch("app.api.contact.email_service.send_ambassador_application_email") as send:
        assert client.post("/api/contact/ambassador", json={**VALID, "email": "nope"}).status_code == 400
        assert (
            client.post("/api/contact/ambassador", json={**VALID, "actuarial_club": "maybe"}).status_code
            == 400
        )
    send.assert_not_called()


def test_honeypot_silently_accepts_without_sending(client):
    with patch("app.api.contact.email_service.send_ambassador_application_email") as send:
        resp = client.post("/api/contact/ambassador", json={**VALID, "website": "spam.example"})

    assert resp.status_code == 200
    send.assert_not_called()


def test_rate_limited_after_five(client):
    with patch("app.api.contact.email_service.send_ambassador_application_email"):
        codes = [client.post("/api/contact/ambassador", json=VALID).status_code for _ in range(6)]

    assert codes == [200] * 5 + [429]


def test_email_body_includes_application(app):
    app.config["SMTP_PASSWORD"] = "x"
    from app.services import email_service

    with patch("app.services.email_service._send_admin_notification") as notify:
        email_service.send_ambassador_application_email(**VALID)

    kwargs = notify.call_args.kwargs
    assert kwargs["subject"] == "Campus Ambassador application: Pat Student (Penn State)"
    assert kwargs["reply_to"] == "pat@psu.edu"
    assert "School: Penn State" in kwargs["body"]
    assert "In actuarial club: Yes" in kwargs["body"]
    assert "Passed P, studying for FM." in kwargs["body"]
    assert "I run the study group." in kwargs["body"]
