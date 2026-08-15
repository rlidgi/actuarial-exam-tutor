from datetime import datetime, timezone

from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    # Stable identity key from the external auth provider (Supabase Auth's
    # `sub` claim, a UUID) -- not the email, so a user changing their email
    # with the provider doesn't orphan this row. String(36), not a Postgres
    # UUID column, so the type stays portable to the sqlite test DB (see
    # tests/conftest.py, which builds schema via create_all(), not migrations).
    external_auth_id = db.Column(db.String(36), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    # Free-trial pool: shared across every exam, not reset per-exam -- once
    # a user has subscribed to any exam, the trial no longer applies to a
    # different, unsubscribed one (see entitlement_service.chat_access_status).
    free_turns_used = db.Column(db.Integer, nullable=False, default=0)

    # Referrals (see app/services/referral_service.py). referral_code is
    # generated lazily on first access, not eagerly at signup, so a user who
    # never shares never burns random-code space. referred_by_id is set
    # exactly once, only when this row is first created (never retroactively
    # on a returning user) -- see referral_service.attach_referrer.
    referral_code = db.Column(db.String(16), unique=True, nullable=True, index=True)
    referred_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    # True forever, from the moment any subscription of this user's first
    # ever goes active -- deliberately not inferred from current Subscription
    # rows (which get overwritten/canceled), so "was this user's referral
    # ever completed" stays correct even after a later cancellation.
    has_ever_subscribed = db.Column(db.Boolean, nullable=False, default=False)

    student_profiles = db.relationship(
        "StudentProfile", back_populates="user", cascade="all, delete-orphan"
    )
    referred_by = db.relationship("User", remote_side=[id])
