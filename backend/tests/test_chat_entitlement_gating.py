from unittest.mock import MagicMock, patch

from app.models import Exam, Message, Session, StudentProfile, User


def _response_with_text(text):
    message_item = MagicMock(type="message")
    return MagicMock(output=[message_item], output_text=text)


def _register_with_exhausted_trial(client, db, email):
    resp = client.post("/api/auth/register", json={"email": email, "password": "secret123"})
    token = resp.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    exam = Exam.query.filter_by(code="P").first()
    if exam is None:
        exam = Exam(code="P", name="Exam P")
        db.session.add(exam)
        db.session.commit()

    client.post("/api/students/profiles", json={"exam_code": "P"}, headers=headers)

    user = User.query.filter_by(email=email).first()
    user.free_turns_used = 6  # FREE_TRIAL_TURNS default
    db.session.commit()

    return headers, user


def test_send_message_blocked_when_trial_exhausted(client, db):
    headers, _ = _register_with_exhausted_trial(client, db, "exhausted@example.com")

    with patch("app.services.tutor_service.OpenAI") as mock_openai:
        resp = client.post(
            "/api/chat/message",
            json={"exam_code": "P", "message": "hello"},
            headers=headers,
        )

        assert resp.status_code == 200
        assert resp.get_json() == {"blocked": "trial_exhausted"}
        mock_openai.return_value.responses.create.assert_not_called()


def test_regenerate_blocked_does_not_destroy_existing_exchange(client, db):
    """A blocked regenerate must not delete the exchange it would have
    replaced -- otherwise the student loses that history permanently with
    nothing to show for it once they regain access."""
    headers, user = _register_with_exhausted_trial(client, db, "exhaustedregen@example.com")
    profile = StudentProfile.query.filter_by(user_id=user.id).first()
    session = Session(student_profile_id=profile.id)
    db.session.add(session)
    db.session.commit()
    db.session.add_all([
        Message(session_id=session.id, role="user", content="what is a random variable?"),
        Message(session_id=session.id, role="assistant", content="Good question..."),
    ])
    db.session.commit()

    resp = client.post("/api/chat/regenerate", json={"exam_code": "P"}, headers=headers)

    assert resp.status_code == 200
    assert resp.get_json() == {"blocked": "trial_exhausted"}

    messages = Message.query.filter_by(session_id=session.id).order_by(Message.created_at).all()
    assert [m.content for m in messages] == [
        "what is a random variable?",
        "Good question...",
    ]


def test_send_message_does_not_block_a_subscribed_user(client, db):
    resp = client.post(
        "/api/auth/register", json={"email": "subbed@example.com", "password": "secret123"}
    )
    token = resp.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    exam = Exam.query.filter_by(code="P").first()
    if exam is None:
        exam = Exam(code="P", name="Exam P")
        db.session.add(exam)
        db.session.commit()
    client.post("/api/students/profiles", json={"exam_code": "P"}, headers=headers)

    user = User.query.filter_by(email="subbed@example.com").first()
    user.free_turns_used = 6
    profile = StudentProfile.query.filter_by(user_id=user.id).first()
    from app.models import Subscription

    db.session.add(Subscription(student_profile_id=profile.id, status="active"))
    db.session.commit()

    with patch("app.services.tutor_service.OpenAI") as mock_openai:
        mock_openai.return_value.responses.create.return_value = _response_with_text("Sure.")
        resp = client.post(
            "/api/chat/message", json={"exam_code": "P", "message": "hi"}, headers=headers
        )

    assert resp.status_code == 200
    assert resp.get_json()["reply"] == "Sure."
