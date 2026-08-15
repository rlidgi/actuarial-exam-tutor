"""Shared by every service that calls the Stripe API directly (billing_service,
referral_service) -- Stripe's SDK is configured via a module-level api_key
attribute, not a per-call parameter, so this has to run before any stripe.*
call in a request.
"""
import stripe
from flask import current_app


def use_api_key() -> None:
    stripe.api_key = current_app.config["STRIPE_SECRET_KEY"]
