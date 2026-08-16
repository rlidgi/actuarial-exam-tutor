from datetime import datetime, timezone

from app.extensions import db

# "What is this about?" -- a single, optional tag on the submission, not a
# required field: see api/feedback.py, every field here is optional, so a
# rating alone (or a message alone) is still a valid submission.
CATEGORIES = ("bug", "feature_request", "ui_ux", "performance", "other")

_RATING_COLUMNS = ("overall_rating", "tutor_quality_rating", "ease_of_use_rating", "value_rating")


class Feedback(db.Model):
    """One row per in-app feedback submission (see api/feedback.py) -- the
    source of truth for aggregate analysis (average rating over time, etc).
    Each submission also fires an immediate best-effort email to admin@ (see
    email_service.send_feedback_email), but that's just for visibility --
    this table is what gets queried for insights.

    Every field is nullable: a submission with only one rating filled in,
    or only a free-text message, is still useful data -- forcing every
    question would just suppress partial feedback instead of collecting it.
    """

    __tablename__ = "feedback"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    overall_rating = db.Column(db.Integer, nullable=True)
    tutor_quality_rating = db.Column(db.Integer, nullable=True)
    ease_of_use_rating = db.Column(db.Integer, nullable=True)
    value_rating = db.Column(db.Integer, nullable=True)
    category = db.Column(db.String(32), nullable=True)
    message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User")

    __table_args__ = tuple(
        db.CheckConstraint(
            f"{col} IS NULL OR ({col} >= 1 AND {col} <= 5)",
            name=f"ck_feedback_{col}_range",
        )
        for col in _RATING_COLUMNS
    )
