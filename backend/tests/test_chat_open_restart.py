from unittest.mock import MagicMock, patch

from app.models import Exam, Message, Session, StudentProfile, User


def _stream_events(text, response_id="resp_1"):
    delta_event = MagicMock(type="response.output_text.delta", delta=text)
    message_item = MagicMock(type="message")
    final_response = MagicMock(id=response_id, output=[message_item], output_text=text)
    completed_event = MagicMock(type="response.completed", response=final_response)
    return [delta_event, completed_event]


def _register_with_profile(client, db, register_user, email):
    resp_json = register_user(email)
    headers = {"Authorization": f"Bearer {resp_json['access_token']}"}

    exam = Exam.query.filter_by(code="P").first()
    if exam is None:
        exam = Exam(code="P", name="Exam P")
        db.session.add(exam)
        db.session.commit()

    client.post("/api/students/profiles", json={"exam_code": "P"}, headers=headers)
    return headers


def _profile_for(email):
    user = User.query.filter_by(email=email).first()
    return StudentProfile.query.filter_by(user_id=user.id).first()


def test_open_chat_requires_auth(client):
    resp = client.post("/api/chat/open?exam=P")
    assert resp.status_code == 401


def test_open_chat_generates_a_greeting_when_nothing_sent_today(client, db, register_user):
    headers = _register_with_profile(client, db, register_user, "open1@example.com")

    with patch("app.services.tutor_service.OpenAI") as mock_openai:
        mock_openai.return_value.responses.create.return_value = _stream_events(
            "Welcome! Let's get started."
        )
        resp = client.post("/api/chat/open?exam=P", headers=headers)

    assert resp.status_code == 200
    messages = resp.get_json()["messages"]
    assert messages == [{"role": "assistant", "content": "Hello! Welcome! Let's get started."}]


def test_open_chat_does_not_regreet_when_today_already_has_messages(client, db, register_user):
    headers = _register_with_profile(client, db, register_user, "open2@example.com")
    profile = _profile_for("open2@example.com")
    session = Session(student_profile_id=profile.id)
    db.session.add(session)
    db.session.commit()
    db.session.add(Message(session_id=session.id, role="user", content="already going"))
    db.session.commit()

    with patch("app.services.tutor_service.OpenAI") as mock_openai:
        resp = client.post("/api/chat/open?exam=P", headers=headers)

    assert resp.status_code == 200
    mock_openai.return_value.responses.create.assert_not_called()
    assert resp.get_json()["messages"] == [{"role": "user", "content": "already going"}]


def test_open_chat_skips_generating_when_trial_exhausted(client, db, register_user):
    headers = _register_with_profile(client, db, register_user, "open3@example.com")
    user = User.query.filter_by(email="open3@example.com").first()
    user.free_turns_used = 6
    db.session.commit()

    with patch("app.services.tutor_service.OpenAI") as mock_openai:
        resp = client.post("/api/chat/open?exam=P", headers=headers)

    assert resp.status_code == 200
    mock_openai.return_value.responses.create.assert_not_called()
    assert resp.get_json()["messages"] == []


def test_restart_chat_always_posts_a_new_message(client, db, register_user):
    headers = _register_with_profile(client, db, register_user, "restart1@example.com")
    profile = _profile_for("restart1@example.com")
    session = Session(student_profile_id=profile.id)
    db.session.add(session)
    db.session.commit()
    db.session.add(Message(session_id=session.id, role="assistant", content="earlier today"))
    db.session.commit()

    with patch("app.services.tutor_service.OpenAI") as mock_openai:
        mock_openai.return_value.responses.create.return_value = _stream_events(
            "We were just working on sample spaces."
        )
        resp = client.post("/api/chat/restart?exam=P", headers=headers)

    assert resp.status_code == 200
    assert resp.get_json()["message"] == {
        "role": "assistant", "content": "Hello! We were just working on sample spaces.",
    }
    assert Message.query.filter_by(session_id=session.id).count() == 2


def test_restart_chat_blocked_when_trial_exhausted(client, db, register_user):
    headers = _register_with_profile(client, db, register_user, "restart2@example.com")
    user = User.query.filter_by(email="restart2@example.com").first()
    user.free_turns_used = 6
    db.session.commit()

    with patch("app.services.tutor_service.OpenAI") as mock_openai:
        resp = client.post("/api/chat/restart?exam=P", headers=headers)

    assert resp.status_code == 200
    assert resp.get_json() == {"blocked": "trial_exhausted"}
    mock_openai.return_value.responses.create.assert_not_called()
