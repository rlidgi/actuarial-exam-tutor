from app.models import Exam, Session, StudentProfile, Topic, User
from app.services import mastery_service, student_service


def _make_profile(db):
    user = User(email="learner2@example.com")
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
