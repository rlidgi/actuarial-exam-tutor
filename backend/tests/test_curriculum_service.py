from datetime import datetime, timedelta, timezone

from app.models import Exam, StudentProfile, Topic, User
from app.services import curriculum_service
from app.services.mastery_service import PerformanceOutcome, apply_mastery_update


def _make_profile(db):
    user = User(email="curric@example.com")
    user.set_password("secret123")
    exam = Exam(code="P", name="Exam P")
    db.session.add_all([user, exam])
    db.session.commit()

    profile = StudentProfile(user_id=user.id, exam_id=exam.id)
    db.session.add(profile)
    db.session.commit()

    return profile, exam


def test_unstudied_topics_prioritized_by_exam_weight(app, db):
    profile, exam = _make_profile(db)
    low = Topic(exam_id=exam.id, name="Low Weight", exam_weight=20.0)
    high = Topic(exam_id=exam.id, name="High Weight", exam_weight=50.0)
    db.session.add_all([low, high])
    db.session.commit()

    topic, reason = curriculum_service.select_next_topic(profile)

    assert topic.name == "High Weight"
    assert "not been studied" in reason


def test_studied_topics_weigh_weakness_against_exam_weight(app, db):
    profile, exam = _make_profile(db)
    low_weight_weak = Topic(exam_id=exam.id, name="Low Weight Weak", exam_weight=10.0)
    high_weight_ok = Topic(exam_id=exam.id, name="High Weight OK", exam_weight=90.0)
    db.session.add_all([low_weight_weak, high_weight_ok])
    db.session.commit()

    # Both studied so neither is "unstudied" -- low_weight_weak is much
    # weaker (10 vs 80), but high_weight_ok's exam weight is 9x larger, so
    # its priority score should still win: (100-80)*90=1800 > (100-10)*10=900.
    apply_mastery_update(profile, low_weight_weak, PerformanceOutcome.CORRECT_INDEPENDENT, 0.9)

    from app.models.mastery import Mastery

    weak_record = Mastery.query.filter_by(
        student_profile_id=profile.id, topic_id=low_weight_weak.id
    ).first()
    weak_record.mastery_score = 10
    ok_record = Mastery(
        student_profile_id=profile.id, topic_id=high_weight_ok.id,
        mastery_score=80, current_difficulty=5,
    )
    db.session.add(ok_record)
    db.session.commit()

    topic, reason = curriculum_service.select_next_topic(profile)

    assert topic.name == "High Weight OK"


def test_decayed_topic_can_outrank_higher_scoring_recent_topic(app, db):
    profile, exam = _make_profile(db)
    stale = Topic(exam_id=exam.id, name="Stale Topic", exam_weight=30.0)
    recent = Topic(exam_id=exam.id, name="Recent Topic", exam_weight=30.0)
    db.session.add_all([stale, recent])
    db.session.commit()

    from app.models.mastery import Mastery

    # Raw mastery alone would favor reviewing "recent" (60 < 70). But
    # "stale" hasn't been touched in 90 days, so decay (capped at 15
    # points) drags its effective mastery down to 55 -- below "recent"'s
    # 60 -- and the ranking should flip.
    old_date = datetime.now(timezone.utc) - timedelta(days=90)
    stale_record = Mastery(
        student_profile_id=profile.id, topic_id=stale.id,
        mastery_score=70, current_difficulty=5, last_reviewed_at=old_date,
    )
    recent_record = Mastery(
        student_profile_id=profile.id, topic_id=recent.id,
        mastery_score=60, current_difficulty=5,
        last_reviewed_at=datetime.now(timezone.utc),
    )
    db.session.add_all([stale_record, recent_record])
    db.session.commit()

    topic, reason = curriculum_service.select_next_topic(profile)

    assert topic.name == "Stale Topic"
    assert "decay" in reason.lower()
