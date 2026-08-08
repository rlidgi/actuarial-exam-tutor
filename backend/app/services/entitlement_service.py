"""Subscription + free-trial eligibility: whether a student can chat with
the tutor right now.
"""
from flask import current_app

from app.extensions import db
from app.models.student import StudentProfile
from app.models.subscription import Subscription
from app.models.user import User

# Stripe's "trialing" is its own free-trial mechanism (a Stripe-side trial
# period on the subscription itself), separate from and unrelated to this
# app's own User.free_turns_used pool -- both count as "currently has access".
ACTIVE_SUBSCRIPTION_STATUSES = ("active", "trialing")


def _is_active(sub: Subscription | None) -> bool:
    return bool(sub and sub.status in ACTIVE_SUBSCRIPTION_STATUSES)


def has_any_active_subscription(user_id: int) -> bool:
    return (
        db.session.query(Subscription.id)
        .join(StudentProfile)
        .filter(StudentProfile.user_id == user_id, Subscription.status.in_(ACTIVE_SUBSCRIPTION_STATUSES))
        .first()
        is not None
    )


def chat_access_status(student_profile: StudentProfile) -> tuple[bool, int, bool]:
    """Whether this profile's user can chat with the tutor on this exam
    right now -- either an active subscription to it, or free-trial turns
    still left.

    The free trial only applies to a user with NO active subscription to
    ANY exam -- once they've subscribed to one, they've already had their
    "try it" moment, so the trial doesn't carry over to a different,
    unsubscribed exam; they'd need to subscribe to that one too.

    Returns (subscribed, free_turns_remaining, has_access)."""
    subscribed = _is_active(student_profile.subscription)
    has_any_subscription = has_any_active_subscription(student_profile.user_id)
    free_turns_remaining = 0
    if not has_any_subscription:
        user = db.session.get(User, student_profile.user_id)
        free_turns_remaining = max(
            0, current_app.config["FREE_TRIAL_TURNS"] - user.free_turns_used
        )
    has_access = subscribed or free_turns_remaining > 0
    return subscribed, free_turns_remaining, has_access


def increment_free_turns_used(student_profile: StudentProfile) -> None:
    user = db.session.get(User, student_profile.user_id)
    user.free_turns_used += 1
    db.session.commit()
