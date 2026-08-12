import json
from datetime import datetime, timezone

from flask import Blueprint, Response, jsonify, request, stream_with_context
from flask_jwt_extended import jwt_required

from app.api.helpers import resolve_profile
from app.extensions import db
from app.models.session import Message, Session
from app.services import entitlement_service, tutor_service, vision_service

bp = Blueprint("chat", __name__)


def _get_or_create_open_session(student_profile) -> Session:
    session = (
        Session.query.filter_by(student_profile_id=student_profile.id, ended_at=None)
        .order_by(Session.started_at.desc())
        .first()
    )
    if session is None:
        session = Session(student_profile_id=student_profile.id)
        db.session.add(session)
        db.session.commit()
    return session


def _delete_last_exchange(session: Session) -> str | None:
    """Deletes the session's last user message and everything after it (its
    assistant reply, if one was persisted) -- the drop-and-reask half of
    regenerate/edit-and-resend. Returns the original user message's text (the
    fallback question for a plain regenerate), or None if the session has no
    user messages at all yet."""
    last_user = (
        Message.query.filter_by(session_id=session.id, role="user")
        .order_by(Message.created_at.desc())
        .first()
    )
    if last_user is None:
        return None
    original_text = last_user.content
    Message.query.filter(
        Message.session_id == session.id, Message.created_at >= last_user.created_at
    ).delete()
    db.session.commit()
    return original_text


def _messages_for_day(student_profile, day) -> list[Message]:
    return (
        Message.query.join(Session, Message.session_id == Session.id)
        .filter(Session.student_profile_id == student_profile.id, db.func.date(Message.created_at) == day)
        .order_by(Message.created_at)
        .all()
    )


def _access_gate(profile):
    """Checked before doing ANY work for a turn -- including, for
    regenerate, before deleting the exchange being replaced. Getting this
    check in after the delete would let a blocked regenerate destroy the
    existing last exchange with nothing to replace it. Returns (subscribed,
    blocked_response); blocked_response is a Flask response to return
    immediately if there's no access right now, else None."""
    subscribed, _, has_access = entitlement_service.chat_access_status(profile)
    if not has_access:
        return subscribed, jsonify(blocked="trial_exhausted")
    return subscribed, None


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


def _run_tutor_turn(profile, session: Session, text: str, subscribed: bool):
    """Runs an already access-gated turn as a streamed SSE response (one
    `data: {"delta": "..."}` event per chunk as the reply comes in, then a
    final `data: {"done": true}`), so the frontend can render the tutor's
    answer as it's generated rather than waiting for the whole thing.
    Draws down the free-trial pool on a successful unsubscribed turn once
    the stream completes."""
    def generate():
        for chunk in tutor_service.handle_message(profile, session, text):
            yield _sse({"delta": chunk})
        if not subscribed:
            entitlement_service.increment_free_turns_used(profile)
        yield _sse({"done": True})

    return Response(stream_with_context(generate()), mimetype="text/event-stream")


def _parse_message_request():
    """The composer posts multipart/form-data whenever a screenshot is
    attached (so the image can ride alongside the text) and plain JSON
    otherwise -- accept both rather than forcing every caller through
    multipart. Returns (exam_code, typed_text, image_file | None)."""
    if request.content_type and request.content_type.startswith("multipart/form-data"):
        return (
            request.form.get("exam_code", "").strip().upper(),
            request.form.get("message", "").strip(),
            request.files.get("image"),
        )
    data = request.get_json(silent=True) or {}
    return data.get("exam_code", "").strip().upper(), data.get("message", "").strip(), None


@bp.post("/message")
@jwt_required()
def send_message():
    exam_code, typed_text, image_file = _parse_message_request()

    profile, error = resolve_profile(exam_code)
    if error:
        return error

    subscribed, blocked = _access_gate(profile)
    if blocked:
        return blocked

    transcribed = ""
    if image_file and image_file.filename:
        if not (image_file.mimetype or "").startswith("image/"):
            return jsonify(error="attached file must be an image"), 400
        image_bytes, mime_type = vision_service.downscale_image(image_file.read())
        transcribed = vision_service.transcribe_image(image_bytes, mime_type)

    # A typed question and an attached screenshot's transcription are both
    # optional inputs -- combine whichever are present into one question.
    text = "\n\n".join(part for part in (typed_text, transcribed) if part)
    if not text:
        return jsonify(error="message is required"), 400

    session = _get_or_create_open_session(profile)
    return _run_tutor_turn(profile, session, text, subscribed)


@bp.post("/open")
@jwt_required()
def open_chat():
    """Called when the chat page loads (not viewing a past day): generates
    the tutor's proactive opening message for today's sitting if nothing's
    been sent yet today, then returns today's full message list either way
    -- also how today's own conversation survives a page reload, since nothing
    else fetches it into the live view."""
    exam_code = request.args.get("exam", "").strip().upper()
    profile, error = resolve_profile(exam_code, missing_message="exam query param is required")
    if error:
        return error

    session = _get_or_create_open_session(profile)
    # A user with no chat access shouldn't cost an API call every time they
    # load the page -- just show whatever's already there, same as today's
    # conversation would look with no side effects at all.
    _, blocked = _access_gate(profile)
    if not blocked:
        tutor_service.open_session_for_today(profile, session)

    today = datetime.now(timezone.utc).date()
    messages = _messages_for_day(profile, today)
    return jsonify(messages=[{"role": m.role, "content": m.content} for m in messages])


@bp.post("/restart")
@jwt_required()
def restart_chat():
    """The "New Conversation" button: the display clears client-side and
    the tutor immediately posts a fresh, same-day restart message -- the
    model sees today's real history alongside the unseen "Hello", so it
    naturally picks the conversation back up rather than re-greeting.
    Underlying memory is untouched."""
    exam_code = request.args.get("exam", "").strip().upper()
    profile, error = resolve_profile(exam_code, missing_message="exam query param is required")
    if error:
        return error

    session = _get_or_create_open_session(profile)
    _, blocked = _access_gate(profile)
    if blocked:
        return jsonify(blocked="trial_exhausted")

    message = tutor_service.restart_conversation(profile, session)
    return jsonify(message={"role": message.role, "content": message.content})


@bp.post("/regenerate")
@jwt_required()
def regenerate():
    data = request.get_json(silent=True) or {}
    exam_code = data.get("exam_code", "").strip().upper()
    edited_message = (data.get("edited_message") or "").strip()

    profile, error = resolve_profile(exam_code)
    if error:
        return error

    subscribed, blocked = _access_gate(profile)
    if blocked:
        return blocked

    session = _get_or_create_open_session(profile)
    original_text = _delete_last_exchange(session)

    text = edited_message or original_text or ""
    if not text:
        return jsonify(error="nothing to regenerate"), 400

    return _run_tutor_turn(profile, session, text, subscribed)


@bp.get("/history/days")
@jwt_required()
def history_days():
    exam_code = request.args.get("exam", "").strip().upper()
    profile, error = resolve_profile(exam_code, missing_message="exam query param is required")
    if error:
        return error

    day_col = db.func.date(Message.created_at)
    rows = (
        db.session.query(day_col)
        .join(Session, Message.session_id == Session.id)
        .filter(Session.student_profile_id == profile.id)
        .distinct()
        .order_by(day_col.desc())
        .all()
    )
    return jsonify(days=[str(r[0]) for r in rows])


@bp.get("/history/day/<date_str>")
@jwt_required()
def history_day(date_str):
    try:
        day = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify(error="date must be YYYY-MM-DD"), 400

    exam_code = request.args.get("exam", "").strip().upper()
    profile, error = resolve_profile(exam_code, missing_message="exam query param is required")
    if error:
        return error

    messages = _messages_for_day(profile, day)
    return jsonify(messages=[{"role": m.role, "content": m.content} for m in messages])
