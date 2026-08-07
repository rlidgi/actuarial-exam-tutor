"""
The tutor orchestrator: a hand-rolled OpenAI tool-calling loop against the
Responses API (client.responses.create), not Chat Completions.

Deliberately not the Assistants/Agents API -- per the architecture decision
in this project, the backend owns conversation state and tool execution
directly rather than handing it to a managed thread/agent runtime, so
context assembly stays under our control (Section 37/48's short-term-memory
and cost discipline) and tool execution stays transactionally tied to our
own DB writes.

Responses API specifically (not Chat Completions) because gpt-5.6-sol
rejects function tools combined with its default reasoning_effort on
/v1/chat/completions -- the only way to keep sol's actual reasoning engaged
during tool-calling turns is the Responses API; forcing reasoning_effort to
"none" on Chat Completions would unblock tools but defeat the reason sol
was chosen over the cheaper tiers.

Within a single turn's tool-calling loop (possibly several round trips
before a final reply), each follow-up call chains via previous_response_id
rather than manually replaying the prior function_call/reasoning items:
reasoning models attach a "reasoning" output item alongside each
function_call, and the API rejects a replayed function_call that doesn't
carry its reasoning item with it. previous_response_id lets OpenAI hold
that bookkeeping server-side for the duration of one turn -- only the new
function_call_output items need to be sent. This does NOT extend to across
turns/messages: input for the *first* call of each new user message is
still rebuilt from our own bounded, DB-backed history (_build_history),
matching Section 37/48's short-term-memory discipline rather than leaning
on OpenAI-side conversation state indefinitely.

Long-term memory (Session.summary) is meant to cover what falls out of that
bounded window. The model is asked to keep it updated via the
save_session_summary tool at natural stopping points, but that's a soft,
judgment-based trigger -- nothing forces it to fire promptly. So there's a
second, deterministic path here too (_maybe_auto_summarize): once enough
messages have accumulated since the last summary, the backend forces a
summarization step itself (a separate, cheap-model call, not the main
tutor conversation) regardless of what the main model does that turn. Set
the threshold equal to MAX_HISTORY_MESSAGES so a message can never fall
into the gap between "no longer in the raw window" and "not yet captured
in any summary."
"""

import json

from flask import current_app
from openai import OpenAI

from app.extensions import db
from app.models.exam import Topic
from app.models.session import Message, Session
from app.models.student import StudentProfile
from app.prompts.tutor_prompt import SYSTEM_PROMPT
from app.services import student_service
from app.tools.dispatch import TOOL_HANDLERS, ToolContext
from app.tools.openai_tools import OPENAI_TOOLS

CHAT_MODEL = "gpt-5.6-sol"
MAX_TOOL_ITERATIONS = 5
MAX_HISTORY_MESSAGES = 20

AUTO_SUMMARY_THRESHOLD = MAX_HISTORY_MESSAGES
AUTO_SUMMARY_MODEL = "gpt-5.6-luna"

FALLBACK_REPLY = (
    "Sorry, I'm having trouble working through that right now -- could you try rephrasing, "
    "or we can come back to this in a moment?"
)


def _client() -> OpenAI:
    return OpenAI(api_key=current_app.config["OPENAI_API_KEY"])


def _build_history(session: Session) -> list[dict]:
    recent = (
        Message.query.filter_by(session_id=session.id)
        .order_by(Message.created_at.desc())
        .limit(MAX_HISTORY_MESSAGES)
        .all()
    )
    recent.reverse()
    return [{"role": m.role, "content": m.content} for m in recent]


def _build_instructions(session: Session) -> str:
    if not session.summary:
        return SYSTEM_PROMPT
    return (
        f"{SYSTEM_PROMPT}\n\n"
        "Session context so far (already summarized from earlier in this conversation -- "
        "build on it, don't ignore it):\n"
        f"{session.summary}"
    )


def _messages_since_last_summary(session: Session) -> int:
    baseline = session.last_summarized_at or session.started_at
    return Message.query.filter(
        Message.session_id == session.id, Message.created_at > baseline
    ).count()


def _auto_summarize(client: OpenAI, profile: StudentProfile, session: Session) -> dict:
    transcript = "\n".join(f"{m['role']}: {m['content']}" for m in _build_history(session))
    prior = f"Existing session summary so far:\n{session.summary}\n\n" if session.summary else ""
    valid_topics = ", ".join(t.name for t in Topic.query.filter_by(exam_id=profile.exam_id).all())

    prompt = (
        f"{prior}Recent conversation transcript:\n{transcript}\n\n"
        "Produce an updated cumulative summary of this tutoring session, as JSON with these keys:\n"
        '"summary": a concise summary that incorporates the existing summary above (if any) plus '
        "what's new in the transcript -- the merged whole, not just the recent transcript alone.\n"
        f'"topics_covered": array of topic names discussed, using ONLY these exact names: {valid_topics}\n'
        '"misconceptions": array of misconceptions the student showed, if any (empty array if none)\n'
        '"recommendations": a short recommendation for what to focus on next'
    )

    response = client.chat.completions.create(
        model=AUTO_SUMMARY_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


def _maybe_auto_summarize(client: OpenAI, profile: StudentProfile, session: Session) -> None:
    if _messages_since_last_summary(session) < AUTO_SUMMARY_THRESHOLD:
        return

    try:
        result = _auto_summarize(client, profile, session)
        student_service.apply_session_summary(
            profile, session,
            summary=result.get("summary") or session.summary or "",
            topics_covered=result.get("topics_covered") or [],
            recommendations=result.get("recommendations") or session.recommendations or "",
            misconceptions=result.get("misconceptions") or [],
        )
    except Exception:
        # Best-effort safety net -- if it fails, the model's own
        # save_session_summary calls are still the primary mechanism.
        current_app.logger.exception("auto-summarize failed")


def _run_tool_call(call, ctx: ToolContext) -> dict:
    handler = TOOL_HANDLERS.get(call.name)
    try:
        args = json.loads(call.arguments or "{}")
        result = handler(args, ctx) if handler else {"error": f"unknown tool {call.name}"}
    except Exception as exc:  # noqa: BLE001 -- tool failures degrade gracefully, per Section 51
        current_app.logger.exception("tool call failed: %s", call.name)
        result = {"error": str(exc)}

    return {"type": "function_call_output", "call_id": call.call_id, "output": json.dumps(result)}


def handle_message(student_profile: StudentProfile, session: Session, user_text: str) -> str:
    db.session.add(Message(session_id=session.id, role="user", content=user_text))
    db.session.commit()

    ctx = ToolContext(student_profile=student_profile, session=session)
    client = _client()

    _maybe_auto_summarize(client, student_profile, session)

    # First call of the turn: fresh input from our own bounded history.
    # Later iterations (still resolving the same user message) chain via
    # previous_response_id instead, sending only new tool outputs.
    next_input: list = _build_history(session)
    previous_response_id: str | None = None

    final_text = FALLBACK_REPLY
    for _ in range(MAX_TOOL_ITERATIONS):
        try:
            response = client.responses.create(
                model=CHAT_MODEL,
                instructions=_build_instructions(session),
                tools=OPENAI_TOOLS,
                input=next_input,
                previous_response_id=previous_response_id,
            )
        except Exception:
            current_app.logger.exception("OpenAI responses call failed")
            break

        function_calls = [item for item in response.output if item.type == "function_call"]

        if not function_calls:
            final_text = response.output_text or FALLBACK_REPLY
            break

        previous_response_id = response.id
        next_input = [_run_tool_call(call, ctx) for call in function_calls]
    else:
        current_app.logger.warning("tutor tool-calling loop hit MAX_TOOL_ITERATIONS")

    db.session.add(Message(session_id=session.id, role="assistant", content=final_text))
    db.session.commit()
    return final_text
