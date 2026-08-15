"""Referral program: codes, attaching a new signup to whoever referred
them, and granting/applying discount rewards on both sides once a referral
actually converts to a paid subscription (not just a signup -- see
handle_first_ever_activation).

Kept separate from billing_service (raw Stripe checkout/webhook plumbing)
and entitlement_service (subscription/free-trial access checks), matching
this codebase's existing one-service-per-concern convention.
"""
import secrets
from datetime import datetime, timezone

import stripe
from flask import current_app
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.referral_reward import ReferralReward
from app.models.user import User
from app.services.stripe_utils import any_stripe_customer_id, use_api_key

# No 0/O/1/I/L -- avoids codes that are ambiguous when read aloud or typed
# from memory (this is a code students will actually share with classmates).
_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
_CODE_LENGTH = 8
_CODE_GENERATION_ATTEMPTS = 5


def _generate_code() -> str:
    return "".join(secrets.choice(_CODE_ALPHABET) for _ in range(_CODE_LENGTH))


def get_or_create_referral_code(user: User) -> str:
    """Generated lazily, not eagerly at signup, so a user who never shares
    never burns random-code space. Collision-retry follows the same
    IntegrityError-catch idiom as user_service.find_or_create_by_external_identity,
    since a SELECT-then-INSERT check would have the same race."""
    if user.referral_code:
        return user.referral_code
    for _ in range(_CODE_GENERATION_ATTEMPTS):
        code = _generate_code()
        user.referral_code = code
        try:
            db.session.commit()
            return code
        except IntegrityError:
            db.session.rollback()
    raise RuntimeError("could not generate a unique referral code")


def find_referrer_by_code(code: str | None) -> User | None:
    if not code:
        return None
    return User.query.filter_by(referral_code=code).first()


def attach_referrer(user: User, referral_code: str | None) -> None:
    """Only ever called for a genuinely brand-new user row (see
    user_service.find_or_create_by_external_identity) -- never retroactively
    on a returning user, which would let someone stack a referral code onto
    an account that already exists. Silently no-ops on an unknown code or a
    self-referral attempt rather than raising, since an invalid/stale code
    in a shared link is a normal, harmless thing to happen."""
    referrer = find_referrer_by_code(referral_code)
    if referrer is None or referrer.id == user.id:
        return
    user.referred_by_id = referrer.id
    db.session.commit()


def completed_referral_count(referrer_id: int) -> int:
    """How many of this user's referrals have actually converted to a paid
    subscription -- signups alone don't count (see has_ever_subscribed)."""
    return User.query.filter_by(referred_by_id=referrer_id, has_ever_subscribed=True).count()


def reward_history(user: User) -> list[ReferralReward]:
    """Every reward this user has ever received -- their own one-time
    referred-user discount, and/or rewards earned referring others -- newest
    first, for the account page."""
    return (
        ReferralReward.query.filter_by(user_id=user.id)
        .order_by(ReferralReward.created_at.desc())
        .all()
    )


def pending_reward_for_checkout(user: User) -> ReferralReward | None:
    """Which reward (if any) should be attached to this user's next Stripe
    Checkout session. Their own one-time "you were referred" discount takes
    priority if it's still unclaimed (it's a hard business requirement tied
    to their first invoice specifically); otherwise, the oldest reward
    they've earned referring others that's still waiting for a subscription
    to attach to. Stripe accepts only one discount per Checkout session, so
    there's always at most one winner."""
    referred_reward = ReferralReward.query.filter_by(
        user_id=user.id, reward_type="referred_percent_off", status="pending"
    ).first()
    if referred_reward is not None:
        return referred_reward
    return (
        ReferralReward.query.filter_by(user_id=user.id, status="pending")
        .order_by(ReferralReward.created_at.asc())
        .first()
    )


def record_referred_user_pending_reward(user: User) -> None:
    """Called at checkout-session creation, before we know whether the
    checkout will actually complete -- records the referred user's first-
    month discount as pending (not applied yet; that happens at activation,
    see handle_first_ever_activation, so an abandoned checkout doesn't
    falsely consume it). Safe to call on a retry after an abandoned
    checkout: the existing pending row is reused, not duplicated."""
    if user.has_ever_subscribed or not user.referred_by_id:
        return
    existing = ReferralReward.query.filter_by(
        user_id=user.id, reward_type="referred_percent_off"
    ).first()
    if existing is not None:
        return
    db.session.add(
        ReferralReward(
            user_id=user.id,
            reward_type="referred_percent_off",
            status="pending",
            stripe_coupon_id=current_app.config["STRIPE_COUPON_REFERRED_25_OFF"],
        )
    )
    db.session.commit()


def grant_referrer_reward(referrer: User, referred_user: User) -> None:
    """Called once a referred user's conversion is confirmed (referred_user
    must already have has_ever_subscribed=True by this point -- see
    handle_first_ever_activation). Every completed referral earns the same
    flat account credit, no tiers.

    Applied immediately as a Stripe customer balance credit if the referrer
    already has a Stripe customer id -- balance credits are additive and
    customer-scoped (not tied to one subscription), so multiple rewards
    earned close together just accumulate correctly instead of one
    overwriting another the way stacking discounts on a single subscription
    would. If the referrer has never subscribed themselves yet (no Stripe
    customer id exists), the reward stays pending and is redeemed as a
    coupon on their own first-ever checkout instead (see
    pending_reward_for_checkout) -- there's no background retry/notification
    job for this in v1."""
    reward = ReferralReward(
        user_id=referrer.id,
        referred_user_id=referred_user.id,
        reward_type="referrer_credit",
        status="pending",
        stripe_coupon_id=current_app.config["STRIPE_COUPON_REFERRER_10_OFF"],
    )
    db.session.add(reward)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        # The unique index on referred_user_id means another concurrent
        # activation (webhook + /sync racing for the same checkout) already
        # granted this referrer their reward for this referral.
        return

    customer_id = any_stripe_customer_id(referrer.id)
    if customer_id is None:
        return  # stays pending, redeemed at the referrer's own first checkout

    use_api_key()
    stripe.Customer.create_balance_transaction(
        customer_id,
        amount=-current_app.config["REFERRAL_CREDIT_CENTS"],
        currency="usd",
        description="Referral reward",
    )
    reward.status = "applied"
    reward.applied_at = datetime.now(timezone.utc)
    db.session.commit()


def handle_first_ever_activation(user_id: int) -> None:
    """Called from billing_service whenever a subscription's status becomes
    active -- but the referral side effects below must only run once per
    user, ever, no matter how many times this fires (the webhook and /sync
    both racing for the same checkout is the normal case, not an edge case).
    The conditional UPDATE below is an atomic "only the caller who actually
    flips the flag wins" guard, the same spirit as the IntegrityError-catch
    race handling in user_service.find_or_create_by_external_identity, just
    via a conditional UPDATE instead of a unique-constraint catch since
    there's no natural constraint to hang this particular race on."""
    rowcount = (
        db.session.query(User)
        .filter(User.id == user_id, User.has_ever_subscribed.is_(False))
        .update({"has_ever_subscribed": True})
    )
    db.session.commit()
    if rowcount != 1:
        return  # already handled by a concurrent activation, or not a first-ever conversion

    user = db.session.get(User, user_id)

    reward = pending_reward_for_checkout(user)
    if reward is not None:
        reward.status = "applied"
        reward.applied_at = datetime.now(timezone.utc)
        db.session.commit()

    if user.referred_by_id:
        referrer = db.session.get(User, user.referred_by_id)
        if referrer is not None:
            grant_referrer_reward(referrer, user)
