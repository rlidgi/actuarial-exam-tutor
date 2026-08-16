from datetime import datetime, timezone

from app.extensions import db

EVENT_TYPES = ("login", "logout")


class UserAuthEvent(db.Model):
    """One row per login/logout event -- the source of truth for the admin
    activity dashboard (see api/admin.py). Login events are recorded from
    auth.py's exchange route (every real sign-in, Google or magic link);
    logout events from the dedicated /api/auth/logout endpoint, called by
    auth-context.tsx's logout() -- there's no other way to observe a
    logout under this app's stateless-JWT auth, since a plain token has no
    server-tracked session to expire. A user who closes the tab/browser
    without signing out never produces a logout event; this table reflects
    explicit sign-outs (including the automatic one on an expired session),
    not "session end" in general."""

    __tablename__ = "user_auth_events"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    event_type = db.Column(db.String(16), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User")

    __table_args__ = (
        db.Index("ix_user_auth_events_user_id_created_at", "user_id", "created_at"),
    )
