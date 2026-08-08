from flask import jsonify
from flask_jwt_extended import get_jwt_identity

from app.services import student_service


def resolve_profile(exam_code: str, *, missing_message: str = "exam_code is required"):
    """Resolves the current JWT user's StudentProfile for exam_code.

    Every authenticated route that needs "the calling user's profile for
    this exam" repeats the same missing-code/lookup/404 sequence -- shared
    here so route bodies stay focused on what they actually do.

    Returns (profile, None) on success, or (None, (response, status)) for
    the caller to return directly on failure."""
    if not exam_code:
        return None, (jsonify(error=missing_message), 400)

    user_id = int(get_jwt_identity())
    try:
        return student_service.get_profile(user_id, exam_code), None
    except student_service.ProfileNotFoundError as exc:
        return None, (jsonify(error=str(exc)), 404)
