from datetime import datetime

from flask import Blueprint, jsonify, request
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


def _handle_tutor_turn(profile, session: Session, text: str):
    """Shared by send_message and regenerate: entitlement-gates the turn
    (subscribed, or free-trial turns remaining), runs it, and draws down
    the free-trial pool on a successful unsubscribed turn -- matching the
    old app's {"blocked": "trial_exhausted"} wire shape so a blocked turn
    is distinguishable from a real error."""
    subscribed, _, has_access = entitlement_service.chat_access_status(profile)
    if not has_access:
        return jsonify(blocked="trial_exhausted")

    reply = tutor_service.handle_message(profile, session, text)
    if not subscribed:
        entitlement_service.increment_free_turns_used(profile)
    return jsonify(session_id=session.id, reply=reply)


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
    return _handle_tutor_turn(profile, session, text)


@bp.post("/regenerate")
@jwt_required()
def regenerate():
    data = request.get_json(silent=True) or {}
    exam_code = data.get("exam_code", "").strip().upper()
    edited_message = (data.get("edited_message") or "").strip()

    profile, error = resolve_profile(exam_code)
    if error:
        return error

    session = _get_or_create_open_session(profile)
    original_text = _delete_last_exchange(session)

    text = edited_message or original_text or ""
    if not text:
        return jsonify(error="nothing to regenerate"), 400

    return _handle_tutor_turn(profile, session, text)


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

    messages = (
        Message.query.join(Session, Message.session_id == Session.id)
        .filter(Session.student_profile_id == profile.id, db.func.date(Message.created_at) == day)
        .order_by(Message.created_at)
        .all()
    )
    return jsonify(messages=[{"role": m.role, "content": m.content} for m in messages])
