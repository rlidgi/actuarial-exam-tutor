"""User lifecycle tied to an external identity provider (currently only
Supabase Auth). Named and keyed generically (`external_auth_id`, not
`supabase_user_id`) so a second provider later doesn't require renaming
this function or the column.
"""
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.user import User


class IdentityConflict(Exception):
    """Raised when a verified identity's email already belongs to a
    different external identity -- never silently merged, see auth.py.
    """


def find_or_create_by_external_identity(external_id: str, email: str) -> User:
    user = User.query.filter_by(external_auth_id=external_id).first()
    if user is not None:
        if user.email != email:
            user.email = email
            db.session.commit()
        return user

    user = User(external_auth_id=external_id, email=email)
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        # A concurrent request for this exact identity (e.g. two
        # near-simultaneous exchange calls from the same sign-in) may have
        # already inserted this row -- that's not a real conflict, just the
        # other side of the same race this request lost. Only a genuinely
        # different external_id already holding this email is a real one.
        existing = User.query.filter_by(external_auth_id=external_id).first()
        if existing is not None:
            return existing
        raise IdentityConflict(
            f"{email} is already linked to a different sign-in method"
        ) from exc
    return user
