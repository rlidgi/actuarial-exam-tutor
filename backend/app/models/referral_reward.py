from datetime import datetime, timezone

from app.extensions import db


class ReferralReward(db.Model):
    """One row per reward ever granted -- an audit trail, not just a
    counter, so "why wasn't I charged the discount" is answerable and
    granting is idempotent (see the unique constraint below and
    referral_service.grant_referrer_reward)."""

    __tablename__ = "referral_rewards"

    id = db.Column(db.Integer, primary_key=True)
    # Who receives this reward.
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    # The referred user whose conversion triggered this reward -- set only
    # for referrer-side rewards (referrer_percent_off/referrer_free_month),
    # null for a referred user's own referred_percent_off row. Unique
    # (where not null) because a given referred user's conversion can only
    # ever grant their referrer one reward, no matter how many times the
    # activation path (webhook + /sync) fires for the same checkout.
    referred_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    reward_type = db.Column(db.String(32), nullable=False)
    status = db.Column(db.String(16), nullable=False, default="pending")
    stripe_coupon_id = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    applied_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", foreign_keys=[user_id])
    referred_user = db.relationship("User", foreign_keys=[referred_user_id])

    __table_args__ = (
        db.Index(
            "uq_referral_rewards_referred_user_id",
            "referred_user_id",
            unique=True,
            sqlite_where=db.text("referred_user_id IS NOT NULL"),
            postgresql_where=db.text("referred_user_id IS NOT NULL"),
        ),
    )
