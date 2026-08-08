from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    # Free-trial pool: shared across every exam, not reset per-exam -- once
    # a user has subscribed to any exam, the trial no longer applies to a
    # different, unsubscribed one (see entitlement_service.chat_access_status).
    free_turns_used = db.Column(db.Integer, nullable=False, default=0)

    student_profiles = db.relationship(
        "StudentProfile", back_populates="user", cascade="all, delete-orphan"
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
