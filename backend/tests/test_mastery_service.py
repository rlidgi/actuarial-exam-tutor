from datetime import datetime, timedelta, timezone

from app.models import Exam, StudentProfile, Topic, User
from app.services.mastery_service import (
    PerformanceOutcome,
    apply_mastery_update,
    decay_for,
    outcome_from_recommended_change,
    record_mastery_assessment,
)


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


def test_outcome_from_recommended_change_buckets_correctly():
    assert outcome_from_recommended_change(8) == PerformanceOutcome.CORRECT_INDEPENDENT
    assert outcome_from_recommended_change(3) == PerformanceOutcome.CORRECT_WITH_ONE_HINT
    assert outcome_from_recommended_change(1) == PerformanceOutcome.CORRECT_WITH_MULTIPLE_HINTS
    assert outcome_from_recommended_change(0) == PerformanceOutcome.INCORRECT_NO_MISCONCEPTION
    assert outcome_from_recommended_change(-1) == PerformanceOutcome.INCORRECT_NO_MISCONCEPTION
    assert (
        outcome_from_recommended_change(-5) == PerformanceOutcome.INCORRECT_WITH_MISCONCEPTION
    )


def test_record_mastery_assessment_applies_bucketed_outcome(app, db):
    profile, topic = _make_profile(db)

    record = record_mastery_assessment(profile, topic, confidence=0.8, recommended_change=8)

    assert record.mastery_score > 0
    assert record.confidence == 0.8


def test_new_mastery_record_starts_at_default_difficulty(app, db):
    profile, topic = _make_profile(db)

    record = apply_mastery_update(
        profile, topic, PerformanceOutcome.CORRECT_WITH_ONE_HINT, llm_confidence=0.5
    )

    assert record.current_difficulty == 5


def test_correct_independent_increases_difficulty(app, db):
    profile, topic = _make_profile(db)

    record = apply_mastery_update(
        profile, topic, PerformanceOutcome.CORRECT_INDEPENDENT, llm_confidence=0.9
    )

    assert record.current_difficulty == 6


def test_incorrect_with_misconception_decreases_difficulty(app, db):
    profile, topic = _make_profile(db)
    apply_mastery_update(profile, topic, PerformanceOutcome.CORRECT_INDEPENDENT, 0.9)

    record = apply_mastery_update(
        profile, topic, PerformanceOutcome.INCORRECT_WITH_MISCONCEPTION, llm_confidence=0.3
    )

    assert record.current_difficulty == 4


def test_difficulty_stays_within_bounds(app, db):
    profile, topic = _make_profile(db)

    for _ in range(20):
        apply_mastery_update(profile, topic, PerformanceOutcome.CORRECT_INDEPENDENT, 1.0)
    record = apply_mastery_update(
        profile, topic, PerformanceOutcome.CORRECT_INDEPENDENT, 1.0
    )
    assert record.current_difficulty == 10

    for _ in range(20):
        apply_mastery_update(
            profile, topic, PerformanceOutcome.INCORRECT_WITH_MISCONCEPTION, 0.1
        )
    record = apply_mastery_update(
        profile, topic, PerformanceOutcome.INCORRECT_WITH_MISCONCEPTION, 0.1
    )
    assert record.current_difficulty == 1
