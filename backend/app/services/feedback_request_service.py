"""One-time "we'd love your feedback" email to each user, about a week
after they register.

send_due is run by the daily scheduled job (.github/workflows/
feedback-emails.yml -> POST /api/emails/feedback-requests/send, see
api/emails.py). It picks every user who registered at least
FEEDBACK_REQUEST_DELAY ago, hasn't been sent the email yet and hasn't
unsubscribed -- so its very first run also covers everyone who registered
before this existed. Sends go out in small batches with a pause between
them (the job calls repeatedly until nothing is left), keeping each request
well under gunicorn's timeout and the mailbox's sending limits.
"""
import time
from datetime import datetime, timedelta, timezone

from flask import current_app
from itsdangerous import BadSignature, URLSafeSerializer

from app.extensions import db
from app.models.user import User
from app.services import email_service

FEEDBACK_REQUEST_DELAY = timedelta(days=7)
DEFAULT_BATCH_SIZE = 20
_SECONDS_BETWEEN_SENDS = 1.0
_UNSUBSCRIBE_SALT = "email-unsubscribe"


def _serializer() -> URLSafeSerializer:
    return URLSafeSerializer(current_app.config["SECRET_KEY"], salt=_UNSUBSCRIBE_SALT)


def unsubscribe_token(user: User) -> str:
    """Signed, non-expiring token identifying the user -- lets the email's
    unsubscribe link work without signing in, without being guessable."""
    return _serializer().dumps(user.id)


def unsubscribe(token: str) -> bool:
    """Opts the token's user out of these emails. False for a bad/tampered
    token or an unknown user."""
    try:
        user_id = _serializer().loads(token)
    except BadSignature:
        return False
    user = db.session.get(User, user_id) if isinstance(user_id, int) else None
    if user is None:
        return False
    if not user.email_opt_out:
        user.email_opt_out = True
        db.session.commit()
    return True


def _due_query(now: datetime):
    cutoff = (now - FEEDBACK_REQUEST_DELAY).replace(tzinfo=None)
    return User.query.filter(
        User.feedback_request_sent_at.is_(None),
        User.email_opt_out.is_(False),
        User.created_at <= cutoff,
    ).order_by(User.created_at, User.id)


def send_due(limit: int = DEFAULT_BATCH_SIZE, dry_run: bool = False) -> dict:
    """Sends up to `limit` due emails. dry_run sends nothing and just
    reports how many are due. Returns counts, including how many are still
    due afterwards so the caller knows whether to call again."""
    now = datetime.now(timezone.utc)
    due = _due_query(now)
    if dry_run:
        return {"dry_run": True, "due": due.count(), "sent": 0, "failed": 0, "remaining": due.count()}

    frontend_url = current_app.config["FRONTEND_URL"]
    backend_url = current_app.config["BACKEND_URL"].rstrip("/")
    sent = failed = 0
    for i, user in enumerate(due.limit(limit).all()):
        if i:
            time.sleep(_SECONDS_BETWEEN_SENDS)
        token = unsubscribe_token(user)
        ok = email_service.send_feedback_request_email(
            user,
            unsubscribe_url=f"{frontend_url}/unsubscribe?token={token}",
            one_click_unsubscribe_url=(
                f"{backend_url}/api/emails/unsubscribe?token={token}" if backend_url else None
            ),
        )
        if ok:
            user.feedback_request_sent_at = datetime.now(timezone.utc)
            db.session.commit()
            sent += 1
        else:
            failed += 1

    # The caller keeps calling while remaining > 0 and the last batch sent
    # something -- a batch that sent nothing (SMTP down) stops the loop
    # instead of retrying the same failures forever.
    remaining = _due_query(now).count()
    return {"dry_run": False, "due": sent + remaining, "sent": sent, "failed": failed,
            "remaining": remaining}
