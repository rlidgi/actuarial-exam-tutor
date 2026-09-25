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


_CLUB_ANSWERS = {"yes", "no", "no_club"}


@bp.post("/ambassador")
def submit_ambassador_application():
    """Public Campus Ambassador application (the /ambassadors page) --
    same no-auth, honeypot and per-IP rate-limit handling as submit()
    above, sharing its window so one IP can't double its budget by
    alternating between the two forms."""
    data = request.get_json(silent=True) or {}
    fields = {
        key: (data.get(key) or "").strip()
        for key in ("name", "email", "school", "graduation_year", "actuarial_club", "exams", "message")
    }
    honeypot = (data.get("website") or "").strip()

    if not all(fields[key] for key in ("name", "email", "school", "exams", "message")):
        return jsonify(error="name, email, school, exams, and message are required"), 400
    if (
        len(fields["name"]) > 200
        or len(fields["email"]) > 320
        or len(fields["school"]) > 200
        or len(fields["graduation_year"]) > 10
        or len(fields["exams"]) > 1000
        or len(fields["message"]) > 5000
    ):
        return jsonify(error="one or more fields are too long"), 400
    if not _EMAIL_RE.match(fields["email"]):
        return jsonify(error="invalid email address"), 400
    if fields["actuarial_club"] and fields["actuarial_club"] not in _CLUB_ANSWERS:
        return jsonify(error="invalid actuarial club answer"), 400

    if honeypot:
        return jsonify(ok=True), 200

    if _rate_limited(request.remote_addr or "unknown"):
        return jsonify(error="too many submissions, please try again later"), 429

    email_service.send_ambassador_application_email(**fields)
    return jsonify(ok=True), 200


# Answers accepted for the club form's "What is 1 plus 2?" bot check.
_HUMAN_CHECK_ANSWERS = {"3", "three"}


@bp.post("/club-sponsorship")
def submit_club_sponsorship():
    """Public Actuarial Club sponsorship request (the landing page's
    Actuarial Clubs section) -- same honeypot and shared per-IP rate limit
    as the forms above, plus a simple "What is 1 plus 2?" question the
    visitor must answer."""
    data = request.get_json(silent=True) or {}
    fields = {
        key: (data.get(key) or "").strip()
        for key in ("name", "email", "university", "event_dates")
    }
    human_check = (data.get("human_check") or "").strip().lower()
    honeypot = (data.get("website") or "").strip()

    if not all(fields.values()):
        return jsonify(error="name, email, university, and event dates are required"), 400
    if (
        len(fields["name"]) > 200
        or len(fields["email"]) > 320
        or len(fields["university"]) > 200
        or len(fields["event_dates"]) > 500
    ):
        return jsonify(error="one or more fields are too long"), 400
    if not _EMAIL_RE.match(fields["email"]):
        return jsonify(error="invalid email address"), 400
    if human_check not in _HUMAN_CHECK_ANSWERS:
        return jsonify(error="That answer to \"What is 1 plus 2?\" isn't right -- please try again."), 400

    if honeypot:
        return jsonify(ok=True), 200

    if _rate_limited(request.remote_addr or "unknown"):
        return jsonify(error="too many submissions, please try again later"), 429

    email_service.send_club_sponsorship_email(**fields)
    return jsonify(ok=True), 200
