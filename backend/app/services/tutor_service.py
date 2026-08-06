"""
The tutor orchestrator: a hand-rolled OpenAI tool-calling loop.

Deliberately not the Assistants/Agents API -- per the architecture decision
in this project, the backend owns conversation state and tool execution
directly rather than handing it to a managed thread/agent runtime, so
context assembly stays under our control (Section 37/48's short-term-memory
and cost discipline) and tool execution stays transactionally tied to our
own DB writes.
"""

import json

from flask import current_app
from openai import OpenAI

from app.extensions import db
from app.models.session import Message, Session
from app.models.student import StudentProfile
from app.prompts.tutor_prompt import SYSTEM_PROMPT
from app.tools.dispatch import TOOL_HANDLERS, ToolContext
from app.tools.openai_tools import OPENAI_TOOLS

CHAT_MODEL = "gpt-5.6-terra"
MAX_TOOL_ITERATIONS = 5
MAX_HISTORY_MESSAGES = 20

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
    return [{"role": "system", "content": SYSTEM_PROMPT}] + [
        {"role": m.role, "content": m.content} for m in recent
    ]


def _run_tool_calls(tool_calls, ctx: ToolContext) -> list[dict]:
    results = []
    for call in tool_calls:
        handler = TOOL_HANDLERS.get(call.function.name)
        try:
            args = json.loads(call.function.arguments or "{}")
            result = handler(args, ctx) if handler else {"error": f"unknown tool {call.function.name}"}
        except Exception as exc:  # noqa: BLE001 -- tool failures degrade gracefully, per Section 51
            current_app.logger.exception("tool call failed: %s", call.function.name)
            result = {"error": str(exc)}

        results.append(
            {"role": "tool", "tool_call_id": call.id, "content": json.dumps(result)}
        )
    return results


def handle_message(student_profile: StudentProfile, session: Session, user_text: str) -> str:
    db.session.add(Message(session_id=session.id, role="user", content=user_text))
    db.session.commit()

    ctx = ToolContext(student_profile=student_profile, session=session)
    messages = _build_history(session)
    client = _client()

    final_text = FALLBACK_REPLY
    for _ in range(MAX_TOOL_ITERATIONS):
        try:
            response = client.chat.completions.create(
                model=CHAT_MODEL, messages=messages, tools=OPENAI_TOOLS
            )
        except Exception:
            current_app.logger.exception("OpenAI chat completion failed")
            break

        choice = response.choices[0].message

        if not choice.tool_calls:
            final_text = choice.content or FALLBACK_REPLY
            break

        messages.append(
            {
                "role": "assistant",
                "content": choice.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in choice.tool_calls
                ],
            }
        )
        messages.extend(_run_tool_calls(choice.tool_calls, ctx))
    else:
        current_app.logger.warning("tutor tool-calling loop hit MAX_TOOL_ITERATIONS")

    db.session.add(Message(session_id=session.id, role="assistant", content=final_text))
    db.session.commit()
    return final_text
