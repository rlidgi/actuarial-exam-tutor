"""Referral program: codes, attaching a new signup to whoever referred
them, and granting/applying discount rewards on both sides once a referral
actually converts to a paid subscription (not just a signup -- see
handle_first_ever_activation).

Kept separate from billing_service (raw Stripe checkout/webhook plumbing)
and entitlement_service (subscription/free-trial access checks), matching
this codebase's existing one-service-per-concern convention.

Partner vanity codes (config.PARTNER_REFERRAL_CODES, e.g. a university's
own "PENNSTATE" code) reuse this entire pipeline unchanged -- same
attach_referrer, same ReferralReward rows, same /account "Total earned"
stat and payout-by-request flow -- just with different discount/credit
terms picked in _partner_terms below. A partner's User row can't be
pre-created before they actually sign in for real: accounts are matched
by external_auth_id (the sign-in provider's own identity), not email, so a
placeholder row would make their real first sign-in collide on the unique
email constraint and permanently lock them out. Set their referral_code
directly in the DB once their real account already exists.
"""
import secrets
from datetime import datetime, timezone

import stripe
from flask import current_app
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.referral_reward import ReferralReward
from app.models.user import User
from app.services.stripe_utils import use_api_key, user_id_for_customer

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


def _partner_terms(referrer: User) -> dict | None:
    """None for a standard referral. Looked up by the referrer's own code,
    not the referred user's, since it's the referrer's identity (e.g. the
    Penn State account) that determines which terms apply."""
    if not referrer.referral_code:
        return None
    return current_app.config["PARTNER_REFERRAL_CODES"].get(referrer.referral_code)


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
    referrer = db.session.get(User, user.referred_by_id)
    partner = _partner_terms(referrer) if referrer else None
    coupon = (
        partner["referred_discount_coupon"]
        if partner
        else current_app.config["STRIPE_COUPON_REFERRED_25_OFF"]
    )
    db.session.add(
        ReferralReward(
            user_id=user.id,
            reward_type="referred_percent_off",
            status="pending",
            stripe_coupon_id=coupon,
        )
    )
    db.session.commit()


def grant_referrer_reward(referrer: User, referred_user: User) -> None:
    """Called once a referred user's conversion is confirmed (referred_user
    must already have has_ever_subscribed=True by this point -- see
    handle_first_ever_activation). Every completed referral earns the same
    flat account credit, no tiers -- except a partner referral code (see
    _partner_terms), which earns its own flat amount instead.

    Always left pending here, regardless of whether the referrer already has
    a Stripe customer id -- it's redeemed later, at whichever comes first:
    a coupon on the referrer's own next Checkout session (see
    pending_reward_for_checkout), or a Stripe balance credit applied right
    before their next invoice is generated (see
    apply_pending_rewards_for_customer, fired from the invoice.upcoming
    webhook). Deliberately not applied immediately: a customer balance
    credit only ever offsets a *future* invoice anyway, so applying it the
    moment the referral converts just commits it earlier than it needs to
    be, with no way for the referrer to request a cash payout instead
    before it's used."""
    partner = _partner_terms(referrer)
    reward = ReferralReward(
        user_id=referrer.id,
        referred_user_id=referred_user.id,
        reward_type="referrer_credit",
        status="pending",
        stripe_coupon_id=(
            partner["referrer_credit_coupon"]
            if partner
            else current_app.config["STRIPE_COUPON_REFERRER_10_OFF"]
        ),
        amount_cents=partner["referrer_credit_cents"] if partner else None,
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


def apply_pending_rewards_for_customer(customer_id: str) -> None:
    """Fired from the invoice.upcoming webhook, a few days before Stripe
    generates a customer's next invoice -- applying the credit here (rather
    than the moment a referral converts) means it lands on that upcoming
    invoice specifically, and gives the referrer a real window beforehand to
    email support and request a Visa/PayPal payout instead (support marks
    that reward some status other than "pending", e.g. "paid_out", so it's
    skipped here rather than double-paid).

    Applies every still-pending referrer_credit reward for this customer in
    one pass -- credits are additive, so this is safe even if several
    rewards accumulated since their last invoice. Each reward's own
    amount_cents wins if set (a partner-code reward -- see
    grant_referrer_reward); otherwise the standard program's flat
    REFERRAL_CREDIT_CENTS applies."""
    user_id = user_id_for_customer(customer_id)
    if user_id is None:
        return

    rewards = ReferralReward.query.filter_by(
        user_id=user_id, reward_type="referrer_credit", status="pending"
    ).all()
    if not rewards:
        return

    use_api_key()
    for reward in rewards:
        stripe.Customer.create_balance_transaction(
            customer_id,
            amount=-(reward.amount_cents or current_app.config["REFERRAL_CREDIT_CENTS"]),
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
