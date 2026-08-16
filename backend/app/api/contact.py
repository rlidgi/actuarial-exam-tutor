import re
import time

from flask import Blueprint, jsonify, request

from app.services import email_service

bp = Blueprint("contact", __name__)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Best-effort, single-process defense against spamming admin@'s inbox --
# there's no rate-limiting library anywhere else in this app, and this is
# the only unauthenticated route that triggers a real email send, so a tiny
# in-memory per-IP window is enough without pulling in Flask-Limiter. Resets
# on deploy/restart; not shared across gunicorn workers -- fine for
# "meaningfully raises the bar", not meant to be airtight.
_RATE_LIMIT_WINDOW_SECONDS = 3600
_RATE_LIMIT_MAX_REQUESTS = 5
_recent_submissions: dict[str, list[float]] = {}


def _rate_limited(ip: str) -> bool:
    now = time.monotonic()
    timestamps = [t for t in _recent_submissions.get(ip, []) if now - t < _RATE_LIMIT_WINDOW_SECONDS]
    timestamps.append(now)
    _recent_submissions[ip] = timestamps
    return len(timestamps) > _RATE_LIMIT_MAX_REQUESTS


@bp.post("")
def submit():
    """Public contact form -- no auth required. `website` is a honeypot
    field (hidden from real users via CSS on the frontend); a filled-in
    value means a bot, and the request is silently accepted without
    actually sending anything so as not to tip the bot off."""
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    message = (data.get("message") or "").strip()
    honeypot = (data.get("website") or "").strip()

    if not name or not email or not message:
        return jsonify(error="name, email, and message are required"), 400
    if len(name) > 200 or len(email) > 320 or len(message) > 5000:
        return jsonify(error="one or more fields are too long"), 400
    if not _EMAIL_RE.match(email):
        return jsonify(error="invalid email address"), 400

    if honeypot:
        return jsonify(ok=True), 200

    if _rate_limited(request.remote_addr or "unknown"):
        return jsonify(error="too many submissions, please try again later"), 429

    email_service.send_contact_email(name, email, message)
    return jsonify(ok=True), 200
