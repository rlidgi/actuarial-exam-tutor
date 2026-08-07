import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from app.models import Exam, Message, Session, StudentProfile, Topic, User
from app.prompts.tutor_prompt import SYSTEM_PROMPT
from app.services import student_service, tutor_service


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


def test_build_instructions_plain_when_no_summary(app, db):
    _, session = _make_profile_and_session(db)

    assert tutor_service._build_instructions(session) == SYSTEM_PROMPT


def test_build_instructions_includes_summary_when_present(app, db):
    _, session = _make_profile_and_session(db)
    session.summary = "Covered Bayes' theorem basics."
    db.session.commit()

    result = tutor_service._build_instructions(session)

    assert "Covered Bayes' theorem basics." in result
    assert "Session context so far" in result
    assert SYSTEM_PROMPT in result


def test_messages_since_last_summary_counts_all_when_never_summarized(app, db):
    _, session = _make_profile_and_session(db)
    for i in range(5):
        db.session.add(Message(session_id=session.id, role="user", content=f"msg {i}"))
    db.session.commit()

    assert tutor_service._messages_since_last_summary(session) == 5


def test_messages_since_last_summary_only_counts_after_last_summary(app, db):
    _, session = _make_profile_and_session(db)
    base = datetime.now(timezone.utc)

    for i in range(3):
        db.session.add(
            Message(session_id=session.id, role="user", content=f"old {i}",
                    created_at=base - timedelta(minutes=10))
        )
    db.session.commit()

    session.last_summarized_at = base - timedelta(minutes=5)
    db.session.commit()

    for i in range(2):
        db.session.add(
            Message(session_id=session.id, role="user", content=f"new {i}", created_at=base)
        )
    db.session.commit()

    assert tutor_service._messages_since_last_summary(session) == 2


def test_maybe_auto_summarize_skips_under_threshold(app, db):
    profile, session = _make_profile_and_session(db)
    db.session.add(Message(session_id=session.id, role="user", content="hi"))
    db.session.commit()

    mock_client = MagicMock()
    tutor_service._maybe_auto_summarize(mock_client, profile, session)

    mock_client.chat.completions.create.assert_not_called()
    assert session.summary is None


def test_maybe_auto_summarize_triggers_over_threshold(app, db):
    profile, session = _make_profile_and_session(db)
    for i in range(tutor_service.AUTO_SUMMARY_THRESHOLD):
        db.session.add(Message(session_id=session.id, role="user", content=f"msg {i}"))
    db.session.commit()

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=json.dumps({
            "summary": "Covered general probability basics.",
            "topics_covered": ["General Probability"],
            "misconceptions": ["confuses independence with mutual exclusivity"],
            "recommendations": "Review Venn diagrams.",
        })))]
    )

    tutor_service._maybe_auto_summarize(mock_client, profile, session)

    assert session.summary == "Covered general probability basics."
    assert session.last_summarized_at is not None
    assert student_service.profile_weaknesses(profile) == [
        "confuses independence with mutual exclusivity"
    ]


def test_maybe_auto_summarize_failure_is_swallowed(app, db):
    profile, session = _make_profile_and_session(db)
    for i in range(tutor_service.AUTO_SUMMARY_THRESHOLD):
        db.session.add(Message(session_id=session.id, role="user", content=f"msg {i}"))
    db.session.commit()

    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = RuntimeError("boom")

    tutor_service._maybe_auto_summarize(mock_client, profile, session)  # must not raise

    assert session.summary is None


def test_handle_message_triggers_auto_summary_when_threshold_crossed(app, db):
    profile, session = _make_profile_and_session(db)
    for i in range(tutor_service.AUTO_SUMMARY_THRESHOLD - 1):
        db.session.add(Message(session_id=session.id, role="user", content=f"msg {i}"))
    db.session.commit()

    with patch("app.services.tutor_service.OpenAI") as mock_openai:
        client = mock_openai.return_value
        client.responses.create.return_value = _response_with_text("Sure, let's continue.")
        client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=json.dumps({
                "summary": "Long conversation about probability.",
                "topics_covered": ["General Probability"],
                "misconceptions": [],
                "recommendations": "Keep practicing.",
            })))]
        )

        reply = tutor_service.handle_message(profile, session, "one more message")

    assert reply == "Sure, let's continue."
    client.chat.completions.create.assert_called_once()
    assert session.summary == "Long conversation about probability."


def test_handle_message_does_not_auto_summarize_under_threshold(app, db):
    profile, session = _make_profile_and_session(db)

    with patch("app.services.tutor_service.OpenAI") as mock_openai:
        client = mock_openai.return_value
        client.responses.create.return_value = _response_with_text("Hi there!")

        tutor_service.handle_message(profile, session, "hello")

    client.chat.completions.create.assert_not_called()
    assert session.summary is None
