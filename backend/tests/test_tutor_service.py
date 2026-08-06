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


def _response_with_text(text):
    message_item = MagicMock(type="message")
    return MagicMock(output=[message_item], output_text=text)


def _response_with_tool_call(name, arguments, call_id="call_1"):
    # MagicMock(name=...) sets the mock's own repr name, not a `.name`
    # attribute -- must be assigned separately.
    call_item = MagicMock(type="function_call", call_id=call_id, arguments=arguments)
    call_item.name = name
    return MagicMock(output=[call_item], output_text="")


def test_handle_message_no_tool_calls_persists_both_messages(app, db):
    profile, session = _make_profile_and_session(db)

    with patch("app.services.tutor_service.OpenAI") as mock_openai:
        client = mock_openai.return_value
        client.responses.create.return_value = _response_with_text(
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
        client.responses.create.side_effect = [
            _response_with_tool_call("select_next_topic", "{}"),
            _response_with_text("You should focus on General Probability next."),
        ]

        reply = tutor_service.handle_message(profile, session, "What should I study?")

    assert reply == "You should focus on General Probability next."
    assert client.responses.create.call_count == 2

    second_call_input = client.responses.create.call_args_list[1].kwargs["input"]
    tool_outputs = [i for i in second_call_input if isinstance(i, dict) and i.get("type") == "function_call_output"]
    assert len(tool_outputs) == 1
    assert "General Probability" in tool_outputs[0]["output"]


def test_handle_message_unknown_tool_reports_error_without_crashing(app, db):
    profile, session = _make_profile_and_session(db)

    with patch("app.services.tutor_service.OpenAI") as mock_openai:
        client = mock_openai.return_value
        client.responses.create.side_effect = [
            _response_with_tool_call("not_a_real_tool", "{}"),
            _response_with_text("Let's continue."),
        ]

        reply = tutor_service.handle_message(profile, session, "hello")

    assert reply == "Let's continue."


def test_handle_message_openai_failure_falls_back_gracefully(app, db):
    profile, session = _make_profile_and_session(db)

    with patch("app.services.tutor_service.OpenAI") as mock_openai:
        client = mock_openai.return_value
        client.responses.create.side_effect = RuntimeError("network error")

        reply = tutor_service.handle_message(profile, session, "hello")

    assert reply == tutor_service.FALLBACK_REPLY
