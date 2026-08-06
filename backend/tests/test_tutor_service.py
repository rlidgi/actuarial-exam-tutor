from unittest.mock import MagicMock, patch

from app.models import Exam, Session, StudentProfile, Topic, User
from app.services import tutor_service


def _make_profile_and_session(db):
    user = User(email="student@example.com")
    user.set_password("secret123")
    exam = Exam(code="P", name="Exam P")
    db.session.add_all([user, exam])
    db.session.commit()

    topic = Topic(exam_id=exam.id, name="General Probability")
    db.session.add(topic)
    db.session.commit()

    profile = StudentProfile(user_id=user.id, exam_id=exam.id)
    db.session.add(profile)
    db.session.commit()

    session = Session(student_profile_id=profile.id)
    db.session.add(session)
    db.session.commit()

    return profile, session


def _completion_with_text(text):
    message = MagicMock(content=text, tool_calls=None)
    return MagicMock(choices=[MagicMock(message=message)])


def _completion_with_tool_call(name, arguments, call_id="call_1"):
    tool_call = MagicMock(id=call_id)
    tool_call.function.name = name
    tool_call.function.arguments = arguments
    message = MagicMock(content=None, tool_calls=[tool_call])
    return MagicMock(choices=[MagicMock(message=message)])


def test_handle_message_no_tool_calls_persists_both_messages(app, db):
    profile, session = _make_profile_and_session(db)

    with patch("app.services.tutor_service.OpenAI") as mock_openai:
        client = mock_openai.return_value
        client.chat.completions.create.return_value = _completion_with_text(
            "Let's start with what you already know about sample spaces."
        )

        reply = tutor_service.handle_message(profile, session, "I don't understand probability.")

    assert reply == "Let's start with what you already know about sample spaces."

    from app.models import Message

    messages = Message.query.filter_by(session_id=session.id).order_by(Message.created_at).all()
    assert [m.role for m in messages] == ["user", "assistant"]
    assert messages[0].content == "I don't understand probability."
    assert messages[1].content == reply


def test_handle_message_executes_tool_call_then_returns_final_text(app, db):
    profile, session = _make_profile_and_session(db)

    with patch("app.services.tutor_service.OpenAI") as mock_openai:
        client = mock_openai.return_value
        client.chat.completions.create.side_effect = [
            _completion_with_tool_call("select_next_topic", "{}"),
            _completion_with_text("You should focus on General Probability next."),
        ]

        reply = tutor_service.handle_message(profile, session, "What should I study?")

    assert reply == "You should focus on General Probability next."
    assert client.chat.completions.create.call_count == 2

    second_call_messages = client.chat.completions.create.call_args_list[1].kwargs["messages"]
    tool_messages = [m for m in second_call_messages if m["role"] == "tool"]
    assert len(tool_messages) == 1
    assert "General Probability" in tool_messages[0]["content"]


def test_handle_message_unknown_tool_reports_error_without_crashing(app, db):
    profile, session = _make_profile_and_session(db)

    with patch("app.services.tutor_service.OpenAI") as mock_openai:
        client = mock_openai.return_value
        client.chat.completions.create.side_effect = [
            _completion_with_tool_call("not_a_real_tool", "{}"),
            _completion_with_text("Let's continue."),
        ]

        reply = tutor_service.handle_message(profile, session, "hello")

    assert reply == "Let's continue."


def test_handle_message_openai_failure_falls_back_gracefully(app, db):
    profile, session = _make_profile_and_session(db)

    with patch("app.services.tutor_service.OpenAI") as mock_openai:
        client = mock_openai.return_value
        client.chat.completions.create.side_effect = RuntimeError("network error")

        reply = tutor_service.handle_message(profile, session, "hello")

    assert reply == tutor_service.FALLBACK_REPLY
