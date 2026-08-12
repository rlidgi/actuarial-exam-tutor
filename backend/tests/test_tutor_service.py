import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from app.models import Exam, Message, Session, StudentProfile, Topic, User
from app.prompts.tutor_prompt import SYSTEM_PROMPT
from app.services import student_service, tutor_service


def _make_profile_and_session(db):
    user = User(email="student@example.com", external_auth_id="ext-student")
    exam = Exam(code="P", name="Exam P")
    db.session.add_all([user, exam])
    db.session.commit()

    # select_next_topic only considers leaf topics (parent_topic_id set).
    parent = Topic(exam_id=exam.id, name="Probability Category")
    db.session.add(parent)
    db.session.commit()

    topic = Topic(exam_id=exam.id, name="General Probability", parent_topic_id=parent.id)
    db.session.add(topic)
    db.session.commit()

    profile = StudentProfile(user_id=user.id, exam_id=exam.id)
    db.session.add(profile)
    db.session.commit()

    session = Session(student_profile_id=profile.id)
    db.session.add(session)
    db.session.commit()

    return profile, session


def _stream_events(deltas, response_id="resp_1"):
    """Simulates client.responses.create(..., stream=True)'s return value
    for a turn that ends in a real answer (no tool calls): one
    response.output_text.delta event per chunk in `deltas` (a single str is
    treated as one chunk), followed by response.completed carrying the
    final Response object -- the shape _run_turn actually consumes."""
    if isinstance(deltas, str):
        deltas = [deltas]
    events = [MagicMock(type="response.output_text.delta", delta=d) for d in deltas]
    message_item = MagicMock(type="message")
    final_response = MagicMock(id=response_id, output=[message_item], output_text="".join(deltas))
    events.append(MagicMock(type="response.completed", response=final_response))
    return events


def _stream_tool_call(name, arguments, call_id="call_1", response_id="resp_1"):
    """Simulates a streamed turn that ends in a function call -- no text
    deltas, just the completed event with a function_call output item."""
    # MagicMock(name=...) sets the mock's own repr name, not a `.name`
    # attribute -- must be assigned separately.
    call_item = MagicMock(type="function_call", call_id=call_id, arguments=arguments)
    call_item.name = name
    final_response = MagicMock(id=response_id, output=[call_item], output_text="")
    return [MagicMock(type="response.completed", response=final_response)]


def _handle_message(profile, session, text):
    """Drains handle_message's stream for tests that just want the final
    reply text, same as calling the old non-streaming version would have."""
    return tutor_service._drain(tutor_service.handle_message(profile, session, text))


def test_handle_message_no_tool_calls_persists_both_messages(app, db):
    profile, session = _make_profile_and_session(db)

    with patch("app.services.tutor_service.OpenAI") as mock_openai:
        client = mock_openai.return_value
        client.responses.create.return_value = _stream_events(
            "Let's start with what you already know about sample spaces."
        )

        reply = _handle_message(profile, session, "I don't understand probability.")

    assert reply == "Let's start with what you already know about sample spaces."

    from app.models import Message

    messages = Message.query.filter_by(session_id=session.id).order_by(Message.created_at).all()
    assert [m.role for m in messages] == ["user", "assistant"]
    assert messages[0].content == "I don't understand probability."
    assert messages[1].content == reply


def test_handle_message_streams_chunks_as_they_arrive(app, db):
    profile, session = _make_profile_and_session(db)

    with patch("app.services.tutor_service.OpenAI") as mock_openai:
        client = mock_openai.return_value
        client.responses.create.return_value = _stream_events(["Sam", "ple ", "spaces."])

        chunks = list(tutor_service.handle_message(profile, session, "hi"))

    assert chunks == ["Sam", "ple ", "spaces."]
    assistant_message = Message.query.filter_by(session_id=session.id, role="assistant").first()
    assert assistant_message.content == "Sample spaces."


def test_handle_message_executes_tool_call_then_returns_final_text(app, db):
    profile, session = _make_profile_and_session(db)

    with patch("app.services.tutor_service.OpenAI") as mock_openai:
        client = mock_openai.return_value
        client.responses.create.side_effect = [
            _stream_tool_call("select_next_topic", "{}"),
            _stream_events("You should focus on General Probability next."),
        ]

        reply = _handle_message(profile, session, "What should I study?")

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
            _stream_tool_call("not_a_real_tool", "{}"),
            _stream_events("Let's continue."),
        ]

        reply = _handle_message(profile, session, "hello")

    assert reply == "Let's continue."


def test_handle_message_openai_failure_falls_back_gracefully(app, db):
    profile, session = _make_profile_and_session(db)

    with patch("app.services.tutor_service.OpenAI") as mock_openai:
        client = mock_openai.return_value
        client.responses.create.side_effect = RuntimeError("network error")

        chunks = list(tutor_service.handle_message(profile, session, "hello"))

    assert chunks == [tutor_service.FALLBACK_REPLY]
    assistant_message = Message.query.filter_by(session_id=session.id, role="assistant").first()
    assert assistant_message.content == tutor_service.FALLBACK_REPLY


def test_build_instructions_plain_when_no_summary(app, db):
    profile, session = _make_profile_and_session(db)

    result = tutor_service._build_instructions(profile, session)

    assert SYSTEM_PROMPT in result
    assert "Probability Category" in result  # this exam's parent-topic name, injected dynamically
    # The phrase itself appears in SYSTEM_PROMPT's own instructions about
    # recognizing an injected summary block -- check for the actual
    # injected block, not just the phrase.
    assert "Session context so far (already summarized" not in result


def test_build_instructions_includes_summary_when_present(app, db):
    profile, session = _make_profile_and_session(db)
    session.summary = "Covered Bayes' theorem basics."
    db.session.commit()

    result = tutor_service._build_instructions(profile, session)

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
    tutor_service._maybe_auto_summarize(mock_client, MagicMock(), profile, session)

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

    tutor_service._maybe_auto_summarize(mock_client, MagicMock(), profile, session)

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

    tutor_service._maybe_auto_summarize(mock_client, MagicMock(), profile, session)  # must not raise

    assert session.summary is None


def test_handle_message_triggers_auto_summary_when_threshold_crossed(app, db):
    profile, session = _make_profile_and_session(db)
    for i in range(tutor_service.AUTO_SUMMARY_THRESHOLD - 1):
        db.session.add(Message(session_id=session.id, role="user", content=f"msg {i}"))
    db.session.commit()

    with patch("app.services.tutor_service.OpenAI") as mock_openai:
        client = mock_openai.return_value
        client.responses.create.return_value = _stream_events("Sure, let's continue.")
        client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=json.dumps({
                "summary": "Long conversation about probability.",
                "topics_covered": ["General Probability"],
                "misconceptions": [],
                "recommendations": "Keep practicing.",
            })))]
        )

        reply = _handle_message(profile, session, "one more message")

    assert reply == "Sure, let's continue."
    client.chat.completions.create.assert_called_once()
    assert session.summary == "Long conversation about probability."


def test_handle_message_does_not_auto_summarize_under_threshold(app, db):
    profile, session = _make_profile_and_session(db)

    with patch("app.services.tutor_service.OpenAI") as mock_openai:
        client = mock_openai.return_value
        client.responses.create.return_value = _stream_events("Hi there!")

        _handle_message(profile, session, "hello")

    client.chat.completions.create.assert_not_called()
    assert session.summary is None


def test_generate_opening_message_sends_an_unseen_hello(app, db):
    profile, session = _make_profile_and_session(db)
    db.session.add(Message(session_id=session.id, role="user", content="earlier today"))
    db.session.commit()

    with patch("app.services.tutor_service.OpenAI") as mock_openai:
        client = mock_openai.return_value
        client.responses.create.return_value = _stream_events("Welcome back!")

        text = tutor_service.generate_opening_message(profile, session)

    assert text == "Welcome back!"
    sent_input = client.responses.create.call_args.kwargs["input"]
    assert sent_input[-1] == {"role": "user", "content": "Hello"}
    assert sent_input[0] == {"role": "user", "content": "earlier today"}
    # Pure -- doesn't persist anything itself, including the "Hello" trigger.
    assert Message.query.filter_by(session_id=session.id).count() == 1


def test_open_session_for_today_generates_and_persists_when_empty(app, db):
    profile, session = _make_profile_and_session(db)

    with patch("app.services.tutor_service.OpenAI") as mock_openai:
        client = mock_openai.return_value
        client.responses.create.return_value = _stream_events("Welcome back! Ready to dive in?")

        tutor_service.open_session_for_today(profile, session)

    messages = Message.query.filter_by(session_id=session.id).all()
    assert len(messages) == 1
    assert messages[0].role == "assistant"
    assert messages[0].content == "Welcome back! Ready to dive in?"


def test_open_session_for_today_is_a_noop_when_today_already_has_messages(app, db):
    profile, session = _make_profile_and_session(db)
    db.session.add(Message(session_id=session.id, role="user", content="already talking"))
    db.session.commit()

    with patch("app.services.tutor_service.OpenAI") as mock_openai:
        client = mock_openai.return_value

        tutor_service.open_session_for_today(profile, session)

    client.responses.create.assert_not_called()
    assert Message.query.filter_by(session_id=session.id).count() == 1


def test_open_session_for_today_recovers_from_concurrent_greeting(app, db):
    """Two near-simultaneous page loads (e.g. React Strict Mode's dev-mode
    double effect invocation) can both see no messages today and both start
    generating a greeting. The loser must not also persist one."""
    profile, session = _make_profile_and_session(db)

    def racing_generate(*args, **kwargs):
        db.session.add(Message(session_id=session.id, role="assistant", content="the winner's greeting"))
        db.session.commit()
        return "the loser's greeting"

    with patch(
        "app.services.tutor_service.generate_opening_message", side_effect=racing_generate
    ):
        tutor_service.open_session_for_today(profile, session)

    messages = Message.query.filter_by(session_id=session.id).all()
    assert len(messages) == 1
    assert messages[0].content == "the winner's greeting"


def test_restart_conversation_always_persists_a_new_message(app, db):
    profile, session = _make_profile_and_session(db)
    db.session.add(Message(session_id=session.id, role="assistant", content="earlier today"))
    db.session.commit()

    with patch("app.services.tutor_service.OpenAI") as mock_openai:
        client = mock_openai.return_value
        client.responses.create.return_value = _stream_events("We were just working on sample spaces.")

        message = tutor_service.restart_conversation(profile, session)

    assert message.content == "We were just working on sample spaces."
    assert Message.query.filter_by(session_id=session.id).count() == 2
