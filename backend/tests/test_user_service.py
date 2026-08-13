import uuid
from unittest.mock import patch

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.services import user_service


def test_find_or_create_recovers_from_concurrent_insert_race(db):
    """Two near-simultaneous exchange calls for the same brand-new sign-in
    (e.g. React's dev-mode double effect invocation, or a double-click)
    both see no existing row and both attempt to insert one. The loser's
    insert fails on the external_auth_id uniqueness constraint -- that must
    resolve to the winner's row, not a false IdentityConflict.
    """
    external_id = str(uuid.uuid4())
    email = "racer@example.com"
    real_commit = db.session.commit

    def racing_commit():
        # Simulate a concurrent request winning the insert race for this
        # exact identity in between this call's own (empty) lookup and its
        # own commit.
        db.session.rollback()
        db.session.add(User(external_auth_id=external_id, email=email))
        real_commit()
        raise IntegrityError("insert", {}, Exception("duplicate key"))

    with patch.object(db.session, "commit", side_effect=racing_commit):
        user, is_new = user_service.find_or_create_by_external_identity(external_id, email)

    assert user.external_auth_id == external_id
    assert User.query.filter_by(external_auth_id=external_id).count() == 1
    # This request lost the race -- the *other* concurrent request is the
    # one that actually created the account, so this side must report
    # is_new=False to avoid double-firing a "new signup" conversion event.
    assert is_new is False


def test_find_or_create_reports_is_new_for_a_brand_new_identity(db):
    user, is_new = user_service.find_or_create_by_external_identity(
        str(uuid.uuid4()), "brandnew@example.com"
    )

    assert user.email == "brandnew@example.com"
    assert is_new is True


def test_find_or_create_reports_not_new_for_a_returning_identity(db):
    external_id = str(uuid.uuid4())
    user_service.find_or_create_by_external_identity(external_id, "returning@example.com")

    user, is_new = user_service.find_or_create_by_external_identity(
        external_id, "returning@example.com"
    )

    assert user.email == "returning@example.com"
    assert is_new is False


def test_find_or_create_still_rejects_a_real_email_conflict(db):
    other_user = User(external_auth_id=str(uuid.uuid4()), email="taken@example.com")
    db.session.add(other_user)
    db.session.commit()

    with pytest.raises(user_service.IdentityConflict):
        user_service.find_or_create_by_external_identity(str(uuid.uuid4()), "taken@example.com")
