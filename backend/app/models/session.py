from datetime import datetime, timezone

from app.extensions import db


class Session(db.Model):
    __tablename__ = "sessions"

    id = db.Column(db.Integer, primary_key=True)
    student_profile_id = db.Column(
        db.Integer, db.ForeignKey("student_profiles.id"), nullable=False
    )
    started_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    ended_at = db.Column(db.DateTime, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    topics_covered = db.Column(db.JSON, nullable=True)  # list[int] of topic ids
    recommendations = db.Column(db.Text, nullable=True)
    # When `summary` was last written (by the model calling save_session_summary,
    # or by tutor_service's deterministic auto-summary safety net). Used to
    # measure how many messages have accumulated since, so a long session can't
    # silently drift past the short-term context window with nothing covering
    # the gap.
    last_summarized_at = db.Column(db.DateTime, nullable=True)

    student_profile = db.relationship("StudentProfile", back_populates="sessions")
    messages = db.relationship(
        "Message", back_populates="session", cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("sessions.id"), nullable=False)
    role = db.Column(db.String(16), nullable=False)  # "user" | "assistant" | "tool"
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    session = db.relationship("Session", back_populates="messages")
