from app.models import Exam, StudentProfile, Topic, User
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
