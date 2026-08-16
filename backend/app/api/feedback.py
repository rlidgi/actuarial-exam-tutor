from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models.user import User
from app.services import email_service, feedback_service

bp = Blueprint("feedback", __name__)


@bp.post("")
@jwt_required()
def submit():
    """In-app feedback, logged-in users only -- see /feedback (a full page,
    not a modal). No honeypot/rate-limit here: the JWT requirement already
    keeps this off-limits to anonymous spam."""
    data = request.get_json(silent=True) or {}
    user = db.session.get(User, int(get_jwt_identity()))

    try:
        feedback = feedback_service.submit_feedback(
            user,
            overall_rating=data.get("overall_rating"),
            tutor_quality_rating=data.get("tutor_quality_rating"),
            ease_of_use_rating=data.get("ease_of_use_rating"),
            value_rating=data.get("value_rating"),
            category=data.get("category"),
            message=data.get("message"),
        )
    except ValueError as exc:
        return jsonify(error=str(exc)), 400

    email_service.send_feedback_email(
        user,
        {field: getattr(feedback, field) for field in
         ("overall_rating", "tutor_quality_rating", "ease_of_use_rating", "value_rating")},
        feedback.category,
        feedback.message,
    )
    return jsonify(ok=True), 200
