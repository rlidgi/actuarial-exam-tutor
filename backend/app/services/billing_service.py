"""Stripe subscription billing: Checkout, customer portal, and webhook
event handling that keeps the Subscription model in sync with Stripe's
view of the world.

Access is sold per exam ($25/mo each), not as one all-access plan, so
every Checkout session and the resulting Stripe objects carry
student_profile_id in metadata -- there's no other way to know which
profile (and therefore which exam) a given subscription is for once it
reaches Stripe's side.
"""
from datetime import datetime, timezone

import stripe
from flask import current_app

from app.extensions import db
from app.models.student import StudentProfile
from app.models.subscription import Subscription


def _use_api_key() -> None:
    stripe.api_key = current_app.config["STRIPE_SECRET_KEY"]


def any_stripe_customer_id(user_id: int) -> str | None:
    """A user should map to exactly one Stripe customer even though they
    can hold up to three subscriptions (one per exam) -- reusing whichever
    customer id any prior subscription already recorded means Checkout
    attaches new exam subscriptions to that same customer instead of
    Stripe minting a new customer per exam."""
    sub = (
        Subscription.query.join(StudentProfile)
        .filter(StudentProfile.user_id == user_id, Subscription.stripe_customer_id.isnot(None))
        .first()
    )
    return sub.stripe_customer_id if sub else None


def create_checkout_session(
    student_profile: StudentProfile,
    email: str,
    price_id: str,
    success_url: str,
    cancel_url: str,
) -> str:
    _use_api_key()
    existing_customer_id = any_stripe_customer_id(student_profile.user_id)
    metadata = {"student_profile_id": str(student_profile.id)}
    kwargs = {"customer": existing_customer_id} if existing_customer_id else {"customer_email": email}
    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        metadata=metadata,
        subscription_data={"metadata": metadata},
        success_url=success_url,
        cancel_url=cancel_url,
        **kwargs,
    )
    return session.url


def create_portal_session(stripe_customer_id: str, return_url: str) -> str:
    _use_api_key()
    session = stripe.billing_portal.Session.create(
        customer=stripe_customer_id, return_url=return_url
    )
    return session.url


def _epoch_to_datetime(epoch):
    return datetime.fromtimestamp(epoch, tz=timezone.utc) if epoch else None


def _period_end(sub_obj) -> datetime | None:
    """current_period_end lives on the subscription's first item, not the
    top-level Subscription object, as of this Stripe API version."""
    items = getattr(sub_obj, "items", None)
    data = getattr(items, "data", None) if items else None
    if not data:
        return None
    return _epoch_to_datetime(getattr(data[0], "current_period_end", None))


def _upsert_by_profile(
    student_profile_id: int, *, stripe_customer_id=None, stripe_subscription_id=None,
    status=None, current_period_end=None,
) -> Subscription:
    sub = Subscription.query.filter_by(student_profile_id=student_profile_id).first()
    if sub is None:
        sub = Subscription(student_profile_id=student_profile_id)
        db.session.add(sub)
    if stripe_customer_id is not None:
        sub.stripe_customer_id = stripe_customer_id
    if stripe_subscription_id is not None:
        sub.stripe_subscription_id = stripe_subscription_id
    if status is not None:
        sub.status = status
    if current_period_end is not None:
        sub.current_period_end = current_period_end
    db.session.commit()
    return sub


def _upsert_by_subscription_id(
    stripe_subscription_id: str, *, status=None, current_period_end=None,
) -> Subscription | None:
    """Used for customer.subscription.* webhook events, which carry the
    Stripe subscription's own id but nothing that maps back to a profile --
    stripe_subscription_id is unique per row, so it's the only reliable key
    for this event type."""
    sub = Subscription.query.filter_by(stripe_subscription_id=stripe_subscription_id).first()
    if sub is None:
        return None  # customer.subscription.updated arrived before checkout.session.completed linked it
    if status is not None:
        sub.status = status
    if current_period_end is not None:
        sub.current_period_end = current_period_end
    db.session.commit()
    return sub


def sync_from_checkout_session(checkout_session_id: str) -> Subscription | None:
    """Called when the browser lands back on the frontend's success page,
    so the subscription is active immediately rather than waiting on
    webhook delivery (which is normally near-instant but not guaranteed to
    beat the browser redirect). The webhook remains the system of record
    for renewals/cancellations that happen later with no browser involved."""
    _use_api_key()
    obj = stripe.checkout.Session.retrieve(checkout_session_id)
    metadata = getattr(obj, "metadata", None)
    student_profile_id = getattr(metadata, "student_profile_id", None)
    if not student_profile_id:
        return None
    subscription_id = getattr(obj, "subscription", None)
    status = "active"
    current_period_end = None
    if subscription_id:
        sub_obj = stripe.Subscription.retrieve(subscription_id)
        status = sub_obj["status"]
        current_period_end = _period_end(sub_obj)
    return _upsert_by_profile(
        int(student_profile_id),
        stripe_customer_id=getattr(obj, "customer", None),
        stripe_subscription_id=subscription_id,
        status=status,
        current_period_end=current_period_end,
    )


def parse_webhook_event(payload: bytes, sig_header: str):
    return stripe.Webhook.construct_event(
        payload, sig_header, current_app.config["STRIPE_WEBHOOK_SECRET"]
    )


def apply_webhook_event(event) -> None:
    """Update the Subscription table to match what this Stripe event says."""
    _use_api_key()
    event_type = event["type"]
    obj = event["data"]["object"]

    if event_type == "checkout.session.completed":
        metadata = getattr(obj, "metadata", None)
        student_profile_id = getattr(metadata, "student_profile_id", None)
        if not student_profile_id:
            return
        subscription_id = getattr(obj, "subscription", None)
        status = "active"
        current_period_end = None
        if subscription_id:
            sub_obj = stripe.Subscription.retrieve(subscription_id)
            status = sub_obj["status"]
            current_period_end = _period_end(sub_obj)
        _upsert_by_profile(
            int(student_profile_id),
            stripe_customer_id=getattr(obj, "customer", None),
            stripe_subscription_id=subscription_id,
            status=status,
            current_period_end=current_period_end,
        )

    elif event_type in ("customer.subscription.updated", "customer.subscription.created"):
        _upsert_by_subscription_id(obj["id"], status=obj["status"], current_period_end=_period_end(obj))

    elif event_type == "customer.subscription.deleted":
        _upsert_by_subscription_id(obj["id"], status="canceled")
