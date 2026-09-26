import hmac

from flask import Blueprint, current_app, jsonify, request

from app.services import feedback_request_service

bp = Blueprint("emails", __name__)


@bp.post("/feedback-requests/send")
def send_feedback_requests():
    """Called by the scheduled GitHub Actions job (.github/workflows/
    feedback-emails.yml) -- not by the app. Guarded by a shared secret in
    the X-Cron-Secret header rather than a user JWT, since no user is
    signed in; with CRON_SECRET unset it's always refused. Body (optional):
    {"dry_run": bool, "limit": int}."""
    secret = current_app.config["CRON_SECRET"]
    provided = request.headers.get("X-Cron-Secret", "")
    if not secret or not hmac.compare_digest(provided, secret):
        return jsonify(error="forbidden"), 403

    data = request.get_json(silent=True) or {}
    limit = data.get("limit", feedback_request_service.DEFAULT_BATCH_SIZE)
    if not isinstance(limit, int) or isinstance(limit, bool) or not (1 <= limit <= 50):
        return jsonify(error="limit must be an integer from 1 to 50"), 400
    result = feedback_request_service.send_due(limit=limit, dry_run=bool(data.get("dry_run")))
    return jsonify(result), 200


@bp.post("/unsubscribe")
def unsubscribe():
    """Public -- the token itself is the proof of identity (signed, see
    feedback_request_service.unsubscribe_token). Accepts the token as a query
    param too, since RFC 8058 one-click unsubscribe (the List-Unsubscribe
    header mail clients use) POSTs to the URL as-is with a form body."""
    data = request.get_json(silent=True) or {}
    token = (data.get("token") or request.args.get("token") or "").strip()
    if not token or not feedback_request_service.unsubscribe(token):
        return jsonify(error="invalid or expired unsubscribe link"), 400
    return jsonify(ok=True), 200
