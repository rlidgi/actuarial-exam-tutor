from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models.session import Session
from app.services import student_service, tutor_service

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


@bp.post("/message")
@jwt_required()
def send_message():
    data = request.get_json(silent=True) or {}
    exam_code = data.get("exam_code", "").strip().upper()
    text = data.get("message", "").strip()

    if not exam_code or not text:
        return jsonify(error="exam_code and message are required"), 400

    user_id = int(get_jwt_identity())
    try:
        profile = student_service.get_profile(user_id, exam_code)
    except student_service.ProfileNotFoundError as exc:
        return jsonify(error=str(exc)), 404

    session = _get_or_create_open_session(profile)
    reply = tutor_service.handle_message(profile, session, text)

    return jsonify(session_id=session.id, reply=reply)
