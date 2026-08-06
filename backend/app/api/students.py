from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.services import student_service

bp = Blueprint("students", __name__)


@bp.post("/profiles")
@jwt_required()
def create_profile():
    data = request.get_json(silent=True) or {}
    exam_code = data.get("exam_code", "").strip().upper()
    if not exam_code:
        return jsonify(error="exam_code is required"), 400

    user_id = int(get_jwt_identity())
    try:
        profile = student_service.create_profile(
            user_id=user_id,
            exam_code=exam_code,
            goals=data.get("goals"),
            experience_level=data.get("experience_level"),
        )
    except ValueError as exc:
        return jsonify(error=str(exc)), 400

    return jsonify(id=profile.id, exam=profile.exam.code), 201


@bp.get("/me")
@jwt_required()
def get_me():
    exam_code = request.args.get("exam", "").strip().upper()
    if not exam_code:
        return jsonify(error="exam query param is required"), 400

    user_id = int(get_jwt_identity())
    try:
        profile = student_service.get_profile(user_id, exam_code)
    except student_service.ProfileNotFoundError as exc:
        return jsonify(error=str(exc)), 404

    return jsonify(
        id=profile.id,
        exam=profile.exam.code,
        goals=profile.goals,
        experience_level=profile.experience_level,
    )


@bp.get("/me/mastery")
@jwt_required()
def get_mastery():
    exam_code = request.args.get("exam", "").strip().upper()
    if not exam_code:
        return jsonify(error="exam query param is required"), 400

    user_id = int(get_jwt_identity())
    try:
        profile = student_service.get_profile(user_id, exam_code)
    except student_service.ProfileNotFoundError as exc:
        return jsonify(error=str(exc)), 404

    return jsonify(mastery=student_service.profile_mastery_summary(profile))


@bp.get("/me/sessions")
@jwt_required()
def get_sessions():
    exam_code = request.args.get("exam", "").strip().upper()
    if not exam_code:
        return jsonify(error="exam query param is required"), 400

    user_id = int(get_jwt_identity())
    try:
        profile = student_service.get_profile(user_id, exam_code)
    except student_service.ProfileNotFoundError as exc:
        return jsonify(error=str(exc)), 404

    sessions = [
        {
            "id": s.id,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "ended_at": s.ended_at.isoformat() if s.ended_at else None,
            "summary": s.summary,
        }
        for s in profile.sessions
    ]
    return jsonify(sessions=sessions)


@bp.get("/me/progress")
@jwt_required()
def get_progress():
    exam_code = request.args.get("exam", "").strip().upper()
    if not exam_code:
        return jsonify(error="exam query param is required"), 400

    user_id = int(get_jwt_identity())
    try:
        profile = student_service.get_profile(user_id, exam_code)
    except student_service.ProfileNotFoundError as exc:
        return jsonify(error=str(exc)), 404

    return jsonify(student_service.profile_progress_summary(profile))
