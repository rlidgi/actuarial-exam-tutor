import stripe
from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required

from app.api.helpers import resolve_profile
from app.services import billing_service, entitlement_service

bp = Blueprint("billing", __name__)


@bp.post("/checkout")
@jwt_required()
def checkout():
    data = request.get_json(silent=True) or {}
    exam_code = data.get("exam_code", "").strip().upper()
    profile, error = resolve_profile(exam_code)
    if error:
        return error

    price_id = current_app.config["STRIPE_PRICE_IDS"].get(exam_code)
    if not price_id:
        return jsonify(error=f"no Stripe price configured for exam {exam_code}"), 400

    frontend_url = current_app.config["FRONTEND_URL"]
    checkout_url = billing_service.create_checkout_session(
        student_profile=profile,
        email=profile.user.email,
        price_id=price_id,
        success_url=f"{frontend_url}/chat?checkout=success&session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{frontend_url}/subscribe?exam={exam_code}",
    )
    return jsonify(url=checkout_url)


@bp.post("/portal")
@jwt_required()
def portal():
    data = request.get_json(silent=True) or {}
    exam_code = data.get("exam_code", "").strip().upper()
    profile, error = resolve_profile(exam_code)
    if error:
        return error

    customer_id = billing_service.any_stripe_customer_id(profile.user_id)
    if not customer_id:
        return jsonify(error="no billing account found for this user yet"), 400

    frontend_url = current_app.config["FRONTEND_URL"]
    portal_url = billing_service.create_portal_session(
        customer_id, return_url=f"{frontend_url}/chat"
    )
    return jsonify(url=portal_url)


@bp.post("/sync")
@jwt_required()
def sync():
    """Called once by the frontend when it lands on the Checkout success
    page, so the subscription is active immediately rather than waiting on
    webhook delivery (see billing_service.sync_from_checkout_session)."""
    data = request.get_json(silent=True) or {}
    checkout_session_id = data.get("session_id", "").strip()
    if not checkout_session_id:
        return jsonify(error="session_id is required"), 400

    billing_service.sync_from_checkout_session(checkout_session_id)
    return jsonify(ok=True)


@bp.post("/webhook")
def webhook():
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature", "")
    try:
        event = billing_service.parse_webhook_event(payload, sig_header)
    except (ValueError, stripe.error.SignatureVerificationError):
        return jsonify(error="invalid signature"), 400

    billing_service.apply_webhook_event(event)
    return jsonify(received=True)


@bp.get("/status")
@jwt_required()
def status():
    exam_code = request.args.get("exam", "").strip().upper()
    profile, error = resolve_profile(exam_code, missing_message="exam query param is required")
    if error:
        return error

    subscribed, free_turns_remaining, _ = entitlement_service.chat_access_status(profile)
    return jsonify(subscribed=subscribed, free_turns_remaining=free_turns_remaining)
