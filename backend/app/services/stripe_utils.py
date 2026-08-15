"""Shared by every service that calls the Stripe API directly (billing_service,
referral_service) -- Stripe's SDK is configured via a module-level api_key
attribute, not a per-call parameter, so this has to run before any stripe.*
call in a request.
"""
import stripe
from flask import current_app

from app.models.student import StudentProfile
from app.models.subscription import Subscription


def use_api_key() -> None:
    stripe.api_key = current_app.config["STRIPE_SECRET_KEY"]


def any_stripe_customer_id(user_id: int) -> str | None:
    """A user should map to exactly one Stripe customer even though they
    can hold up to three subscriptions (one per exam) -- reusing whichever
    customer id any prior subscription already recorded means Checkout
    attaches new exam subscriptions to that same customer instead of Stripe
    minting a new customer per exam. Kept here (not in billing_service)
    specifically so referral_service can also use it without a circular
    import between the two services."""
    sub = (
        Subscription.query.join(StudentProfile)
        .filter(StudentProfile.user_id == user_id, Subscription.stripe_customer_id.isnot(None))
        .first()
    )
    return sub.stripe_customer_id if sub else None
