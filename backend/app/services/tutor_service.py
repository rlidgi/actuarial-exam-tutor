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

Tracing: every turn, model call, tool call, and auto-summarize is
instrumented via Langfuse (manual spans, not the automatic OpenAI-SDK
wrapper -- that wrapper's documented coverage is chat.completions, and
doesn't confirm support for the Responses API or previous_response_id
chaining this module actually uses, so wrapping our own call sites
precisely is more reliable than trusting auto-instrumentation to catch
everything). Tracing is optional: if LANGFUSE_PUBLIC_KEY/SECRET_KEY aren't
set, the client is constructed with tracing disabled and every call below
is a no-op -- the app runs the same either way.
"""

import json

from flask import current_app
from langfuse import Langfuse
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


_tracer_instance: Langfuse | None = None


def _tracer() -> Langfuse:
    # A cached singleton, not a fresh client per call: Langfuse spins up
    # background export threads at construction time, and a client
    # constructed fresh on every request gets abandoned (along with its
    # in-flight batch) as soon as the request returns, before those threads
    # get a real chance to send anything -- traces silently never arrive,
    # no error raised. One long-lived client per process, matching the
    # SDK's own documented get_client() singleton pattern.
    global _tracer_instance
    if _tracer_instance is None:
        public_key = current_app.config["LANGFUSE_PUBLIC_KEY"]
        secret_key = current_app.config["LANGFUSE_SECRET_KEY"]
        _tracer_instance = Langfuse(
            public_key=public_key or None,
            secret_key=secret_key or None,
            # base_url, not host -- the OTLP span exporter reads base_url
            # specifically; host alone gets credentials that authenticate
            # fine against the REST API but silently fail (401) on export.
            base_url=current_app.config["LANGFUSE_HOST"],
            tracing_enabled=bool(public_key and secret_key),
        )
    return _tracer_instance


def _usage_details(response) -> dict[str, int] | None:
    usage = getattr(response, "usage", None)
    if usage is None:
        return None
    details = {
        "input": getattr(usage, "input_tokens", None),
        "output": getattr(usage, "output_tokens", None),
    }
    return {k: v for k, v in details.items() if v is not None} or None


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


def _auto_summarize(client: OpenAI, tracer: Langfuse, profile: StudentProfile, session: Session) -> dict:
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

    with tracer.start_as_current_observation(
        name="auto_summarize", as_type="generation", model=AUTO_SUMMARY_MODEL, input=prompt,
    ) as gen:
        response = client.chat.completions.create(
            model=AUTO_SUMMARY_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        gen.update(output=content, usage_details=_usage_details(response))

    return json.loads(content)


def _maybe_auto_summarize(
    client: OpenAI, tracer: Langfuse, profile: StudentProfile, session: Session
) -> None:
    if _messages_since_last_summary(session) < AUTO_SUMMARY_THRESHOLD:
        return

    try:
        result = _auto_summarize(client, tracer, profile, session)
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


def _run_tool_call(call, ctx: ToolContext, tracer: Langfuse) -> dict:
    args = json.loads(call.arguments or "{}")

    with tracer.start_as_current_observation(
        name=call.name, as_type="tool", input=args,
    ) as tool_span:
        handler = TOOL_HANDLERS.get(call.name)
        try:
            result = handler(args, ctx) if handler else {"error": f"unknown tool {call.name}"}
        except Exception as exc:  # noqa: BLE001 -- tool failures degrade gracefully, per Section 51
            current_app.logger.exception("tool call failed: %s", call.name)
            result = {"error": str(exc)}
            tool_span.update(output=result, level="ERROR", status_message=str(exc))
        else:
            tool_span.update(output=result)

    return {"type": "function_call_output", "call_id": call.call_id, "output": json.dumps(result)}


def handle_message(student_profile: StudentProfile, session: Session, user_text: str) -> str:
    db.session.add(Message(session_id=session.id, role="user", content=user_text))
    db.session.commit()

    ctx = ToolContext(student_profile=student_profile, session=session)
    client = _client()
    tracer = _tracer()

    with tracer.start_as_current_observation(
        name="tutor_turn",
        as_type="span",
        input=user_text,
        metadata={
            "student_profile_id": student_profile.id,
            "session_id": session.id,
            "exam_code": student_profile.exam.code,
        },
    ) as turn_span:
        _maybe_auto_summarize(client, tracer, student_profile, session)

        # First call of the turn: fresh input from our own bounded history.
        # Later iterations (still resolving the same user message) chain via
        # previous_response_id instead, sending only new tool outputs.
        next_input: list = _build_history(session)
        previous_response_id: str | None = None

        final_text = FALLBACK_REPLY
        for _ in range(MAX_TOOL_ITERATIONS):
            with tracer.start_as_current_observation(
                name="tutor_model_call", as_type="generation", model=CHAT_MODEL,
                input={"input": next_input, "previous_response_id": previous_response_id},
            ) as gen:
                try:
                    response = client.responses.create(
                        model=CHAT_MODEL,
                        instructions=_build_instructions(session),
                        tools=OPENAI_TOOLS,
                        input=next_input,
                        previous_response_id=previous_response_id,
                    )
                except Exception as exc:
                    current_app.logger.exception("OpenAI responses call failed")
                    gen.update(level="ERROR", status_message=str(exc))
                    break

                function_calls = [item for item in response.output if item.type == "function_call"]
                gen.update(
                    output=(
                        response.output_text if not function_calls
                        else [{"tool": c.name, "arguments": c.arguments} for c in function_calls]
                    ),
                    usage_details=_usage_details(response),
                )

            if not function_calls:
                final_text = response.output_text or FALLBACK_REPLY
                break

            previous_response_id = response.id
            next_input = [_run_tool_call(call, ctx, tracer) for call in function_calls]
        else:
            current_app.logger.warning("tutor tool-calling loop hit MAX_TOOL_ITERATIONS")

        turn_span.update(output=final_text)

    tracer.flush()

    db.session.add(Message(session_id=session.id, role="assistant", content=final_text))
    db.session.commit()
    return final_text
