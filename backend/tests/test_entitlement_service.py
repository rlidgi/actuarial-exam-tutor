from app.models import Exam, StudentProfile, Subscription, User
from app.services import entitlement_service


def _make_profile(db, email="entitle@example.com"):
    user = User(email=email)
    user.set_password("secret123")
    exam = Exam.query.filter_by(code="P").first()
    if exam is None:
        exam = Exam(code="P", name="Exam P")
        db.session.add(exam)
        db.session.commit()
    db.session.add(user)
    db.session.commit()

    profile = StudentProfile(user_id=user.id, exam_id=exam.id)
    db.session.add(profile)
    db.session.commit()
    return user, profile


def test_chat_access_status_unsubscribed_user_gets_free_trial(app, db):
    _, profile = _make_profile(db)

    subscribed, remaining, has_access = entitlement_service.chat_access_status(profile)

    assert subscribed is False
    assert remaining == app.config["FREE_TRIAL_TURNS"]
    assert has_access is True


def test_chat_access_status_exhausted_trial_has_no_access(app, db):
    user, profile = _make_profile(db)
    user.free_turns_used = app.config["FREE_TRIAL_TURNS"]
    db.session.commit()

    subscribed, remaining, has_access = entitlement_service.chat_access_status(profile)

    assert subscribed is False
    assert remaining == 0
    assert has_access is False


def test_chat_access_status_active_subscription_has_access_regardless_of_trial(app, db):
    user, profile = _make_profile(db)
    user.free_turns_used = app.config["FREE_TRIAL_TURNS"]
    db.session.add(Subscription(student_profile_id=profile.id, status="active"))
    db.session.commit()

    subscribed, remaining, has_access = entitlement_service.chat_access_status(profile)

    assert subscribed is True
    assert has_access is True


def test_chat_access_status_trialing_counts_as_subscribed(app, db):
    _, profile = _make_profile(db)
    db.session.add(Subscription(student_profile_id=profile.id, status="trialing"))
    db.session.commit()

    subscribed, _, has_access = entitlement_service.chat_access_status(profile)

    assert subscribed is True
    assert has_access is True


def test_chat_access_status_canceled_subscription_does_not_count(app, db):
    _, profile = _make_profile(db)
    db.session.add(Subscription(student_profile_id=profile.id, status="canceled"))
    db.session.commit()

    subscribed, remaining, has_access = entitlement_service.chat_access_status(profile)

    assert subscribed is False
    assert remaining == app.config["FREE_TRIAL_TURNS"]
    assert has_access is True


def test_chat_access_status_trial_does_not_carry_to_unsubscribed_second_exam(app, db):
    """Once a user has subscribed to ANY exam, the free trial no longer
    applies to a different, unsubscribed exam -- they'd need to subscribe
    to that one too."""
    user, p_profile = _make_profile(db, email="multiexam@example.com")
    db.session.add(Subscription(student_profile_id=p_profile.id, status="active"))

    fm_exam = Exam(code="FM", name="Exam FM")
    db.session.add(fm_exam)
    db.session.commit()
    fm_profile = StudentProfile(user_id=user.id, exam_id=fm_exam.id)
    db.session.add(fm_profile)
    db.session.commit()

    subscribed, remaining, has_access = entitlement_service.chat_access_status(fm_profile)

    assert subscribed is False
    assert remaining == 0
    assert has_access is False


def test_increment_free_turns_used(db):
    user, profile = _make_profile(db)
    assert user.free_turns_used == 0

    entitlement_service.increment_free_turns_used(profile)
    entitlement_service.increment_free_turns_used(profile)

    assert user.free_turns_used == 2
