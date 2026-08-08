from unittest.mock import MagicMock, patch

from app.models import Exam, Message, Session, StudentProfile, User


def _response_with_text(text):
    message_item = MagicMock(type="message")
    return MagicMock(output=[message_item], output_text=text)


def _register(client, email):
    resp = client.post("/api/auth/register", json={"email": email, "password": "secret123"})
    token = resp.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _make_profile_with_exchange(db, email):
    user = User.query.filter_by(email=email).first()
    exam = Exam(code="P", name="Exam P")
    db.session.add(exam)
    db.session.commit()

    profile = StudentProfile(user_id=user.id, exam_id=exam.id)
    db.session.add(profile)
    db.session.commit()

    session = Session(student_profile_id=profile.id)
    db.session.add(session)
    db.session.commit()

    db.session.add_all([
        Message(session_id=session.id, role="user", content="what is a random variable?"),
        Message(session_id=session.id, role="assistant", content="Good question -- let's start..."),
    ])
    db.session.commit()

    return profile, session


def test_regenerate_requires_auth(client):
    resp = client.post("/api/chat/regenerate", json={"exam_code": "P"})
    assert resp.status_code == 401


def test_regenerate_replaces_last_exchange_with_same_question(client, db):
    headers = _register(client, "regen@example.com")
    profile, session = _make_profile_with_exchange(db, "regen@example.com")

    with patch("app.services.tutor_service.OpenAI") as mock_openai:
        mock_client = mock_openai.return_value
        mock_client.responses.create.return_value = _response_with_text("A fresh explanation.")

        resp = client.post(
            "/api/chat/regenerate", json={"exam_code": "P"}, headers=headers
        )

    assert resp.status_code == 200
    assert resp.get_json()["reply"] == "A fresh explanation."

    messages = (
        Message.query.filter_by(session_id=session.id).order_by(Message.created_at).all()
    )
    assert [m.content for m in messages] == [
        "what is a random variable?",
        "A fresh explanation.",
    ]

    # The regenerated call actually re-asked the original question.
    sent_input = mock_client.responses.create.call_args.kwargs["input"]
    assert sent_input[0]["content"] == "what is a random variable?"


def test_regenerate_with_edited_message_replaces_question(client, db):
    headers = _register(client, "regenedit@example.com")
    _, session = _make_profile_with_exchange(db, "regenedit@example.com")

    with patch("app.services.tutor_service.OpenAI") as mock_openai:
        mock_client = mock_openai.return_value
        mock_client.responses.create.return_value = _response_with_text("Answering the edit.")

        resp = client.post(
            "/api/chat/regenerate",
            json={"exam_code": "P", "edited_message": "what is a discrete random variable?"},
            headers=headers,
        )

    assert resp.status_code == 200

    messages = (
        Message.query.filter_by(session_id=session.id).order_by(Message.created_at).all()
    )
    assert [m.content for m in messages] == [
        "what is a discrete random variable?",
        "Answering the edit.",
    ]


def test_regenerate_with_nothing_to_regenerate_returns_400(client, db):
    headers = _register(client, "regenempty@example.com")
    user = User.query.filter_by(email="regenempty@example.com").first()
    exam = Exam(code="P", name="Exam P")
    db.session.add(exam)
    db.session.commit()
    profile = StudentProfile(user_id=user.id, exam_id=exam.id)
    db.session.add(profile)
    db.session.commit()

    resp = client.post("/api/chat/regenerate", json={"exam_code": "P"}, headers=headers)

    assert resp.status_code == 400
