from unittest.mock import patch

from sqlalchemy.exc import IntegrityError

from app.models import Exam, Session, StudentProfile, Topic, User
from app.services import mastery_service, student_service


def test_create_profile_recovers_from_concurrent_insert_race(app, db):
    """Two near-simultaneous ensureProfile calls for the same brand-new
    sign-in (e.g. React's dev-mode double effect invocation) both see no
    existing profile and both attempt to insert one. The loser's insert
    fails on the (user_id, exam_id) uniqueness constraint -- that must
    resolve to the winner's row, not an unhandled 500.
    """
    user = User(email="racer2@example.com", external_auth_id="ext-racer2")
    exam = Exam(code="P", name="Exam P")
    db.session.add_all([user, exam])
    db.session.commit()

    real_commit = db.session.commit

    def racing_commit():
        # Simulate a concurrent request winning the insert race for this
        # exact (user_id, exam_id) pair in between this call's own (empty)
        # lookup and its own commit.
        db.session.rollback()
        db.session.add(StudentProfile(user_id=user.id, exam_id=exam.id))
        real_commit()
        raise IntegrityError("insert", {}, Exception("duplicate key"))

    with patch.object(db.session, "commit", side_effect=racing_commit):
        profile = student_service.create_profile(user_id=user.id, exam_code="P")

    assert profile.user_id == user.id
    assert profile.exam_id == exam.id
    assert StudentProfile.query.filter_by(user_id=user.id, exam_id=exam.id).count() == 1


def _make_profile(db):
    user = User(email="learner2@example.com", external_auth_id="ext-learner2")
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


def test_record_mistake_creates_with_low_severity(app, db):
    profile, topic = _make_profile(db)

    mistake = student_service.record_mistake(profile, topic.id, "confuses P(A|B) with P(B|A)")

    assert mistake.frequency == 1
    assert mistake.severity == "low"


def test_record_mistake_escalates_severity_with_frequency(app, db):
    profile, topic = _make_profile(db)

    for _ in range(4):
        mistake = student_service.record_mistake(
            profile, topic.id, "confuses P(A|B) with P(B|A)"
        )

    assert mistake.frequency == 4
    assert mistake.severity == "high"


def test_profile_difficulty_summary_reflects_mastery_records(app, db):
    profile, topic = _make_profile(db)
    mastery_service.apply_mastery_update(
        profile, topic, mastery_service.PerformanceOutcome.CORRECT_INDEPENDENT, 0.9
    )

    result = student_service.profile_difficulty_summary(profile)

    assert result == {"Bayes Theorem": 6}


def test_apply_session_summary_persists_fields_and_sets_timestamp(app, db):
    profile, topic = _make_profile(db)
    session = Session(student_profile_id=profile.id)
    db.session.add(session)
    db.session.commit()

    assert session.last_summarized_at is None

    student_service.apply_session_summary(
        profile, session,
        summary="Covered Bayes' theorem basics.",
        topics_covered=["Bayes Theorem"],
        recommendations="Practice more base-rate problems.",
        misconceptions=[],
    )

    assert session.summary == "Covered Bayes' theorem basics."
    assert session.recommendations == "Practice more base-rate problems."
    assert session.last_summarized_at is not None


def test_apply_session_summary_records_misconceptions(app, db):
    profile, topic = _make_profile(db)
    session = Session(student_profile_id=profile.id)
    db.session.add(session)
    db.session.commit()

    student_service.apply_session_summary(
        profile, session,
        summary="...",
        topics_covered=["Bayes Theorem"],
        recommendations="...",
        misconceptions=["confuses P(A|B) with P(B|A)"],
    )

    assert student_service.profile_weaknesses(profile) == ["confuses P(A|B) with P(B|A)"]


def test_apply_session_summary_ignores_unmatched_topic_names(app, db):
    profile, topic = _make_profile(db)
    session = Session(student_profile_id=profile.id)
    db.session.add(session)
    db.session.commit()

    # Should not raise even though "Not A Real Topic" doesn't match any row.
    student_service.apply_session_summary(
        profile, session,
        summary="...",
        topics_covered=["Not A Real Topic"],
        recommendations="...",
        misconceptions=["some misconception"],
    )

    assert student_service.profile_weaknesses(profile) == []
