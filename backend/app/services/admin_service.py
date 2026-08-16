import logging

from app.extensions import db
from app.models.user import User
from app.models.user_auth_event import UserAuthEvent

logger = logging.getLogger(__name__)


def record_login(user: User) -> None:
    """Called from auth.py's exchange route on every real sign-in.
    Best-effort, same reasoning as email_service's sends -- an activity-log
    write must never break the sign-in it's observing."""
    _record_event(user, "login")


def record_logout(user: User) -> None:
    """Called from the /api/auth/logout endpoint, itself only ever called
    for this one purpose -- see auth-context.tsx's logout()."""
    _record_event(user, "logout")


def _record_event(user: User, event_type: str) -> None:
    try:
        db.session.add(UserAuthEvent(user_id=user.id, event_type=event_type))
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception("failed to record %s event for user %s", event_type, user.id)


def list_users_with_activity() -> list[dict]:
    """Everything the admin dashboard's user table needs: every registered
    user plus their most recent login/logout time, if any. One GROUP BY
    query for the latest event per (user, type), merged in Python rather
    than a correlated subquery -- simplest thing that works at this app's
    current scale (see UserAuthEvent)."""
    users = User.query.order_by(User.created_at.desc()).all()

    latest = (
        db.session.query(
            UserAuthEvent.user_id,
            UserAuthEvent.event_type,
            db.func.max(UserAuthEvent.created_at),
        )
        .group_by(UserAuthEvent.user_id, UserAuthEvent.event_type)
        .all()
    )
    last_by_user_and_type = {(user_id, event_type): ts for user_id, event_type, ts in latest}

    return [
        {
            "id": u.id,
            "email": u.email,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_login_at": _isoformat(last_by_user_and_type.get((u.id, "login"))),
            "last_logout_at": _isoformat(last_by_user_and_type.get((u.id, "logout"))),
        }
        for u in users
    ]


def _isoformat(dt):
    return dt.isoformat() if dt else None
