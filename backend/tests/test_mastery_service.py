from datetime import datetime, timedelta, timezone

from app.models import Exam, StudentProfile, Topic, User
from app.services.mastery_service import PerformanceOutcome, apply_mastery_update, decay_for


def _make_profile(db):
    user = User(email="learner@example.com")
    user.set_password("secret123")
    exam = Exam(code="P", name="Exam P")
    db.session.add_all([user, exam])
    db.session.commit()

    topic = Topic(exam_id=exam.id, name="Bayes Theorem")
    db.session.add(topic)
    db.session.commit()

    profile = StudentProfile(user_id=user.id, exam_id=exam.id)
    db.session.add(profile)
    db.session.commit()

    return profile, topic


def test_correct_independent_increases_mastery(app, db):
    profile, topic = _make_profile(db)

    record = apply_mastery_update(
        profile, topic, PerformanceOutcome.CORRECT_INDEPENDENT, llm_confidence=0.9
    )

    assert record.mastery_score > 0
    assert record.mastery_score <= 100


def test_incorrect_with_misconception_can_decrease_mastery(app, db):
    profile, topic = _make_profile(db)
    apply_mastery_update(profile, topic, PerformanceOutcome.CORRECT_INDEPENDENT, 0.9)
    before = apply_mastery_update(
        profile, topic, PerformanceOutcome.CORRECT_INDEPENDENT, 0.9
    ).mastery_score

    after = apply_mastery_update(
        profile, topic, PerformanceOutcome.INCORRECT_WITH_MISCONCEPTION, llm_confidence=0.3
    ).mastery_score

    assert after < before


def test_mastery_score_stays_within_bounds(app, db):
    profile, topic = _make_profile(db)

    for _ in range(30):
        apply_mastery_update(profile, topic, PerformanceOutcome.CORRECT_INDEPENDENT, 1.0)

    record = apply_mastery_update(
        profile, topic, PerformanceOutcome.CORRECT_INDEPENDENT, 1.0
    )
    assert record.mastery_score == 100


def test_decay_is_zero_within_grace_period():
    last_reviewed = datetime.now(timezone.utc) - timedelta(days=5)
    assert decay_for(last_reviewed) == 0


def test_decay_grows_after_grace_period():
    last_reviewed = datetime.now(timezone.utc) - timedelta(days=30)
    assert decay_for(last_reviewed) > 0
