from app.extensions import db
from app.models.exam import Exam, Topic
from app.models.mistake import Mistake
from app.models.session import Session
from app.models.student import StudentProfile
from app.services.curriculum_service import select_next_topic


class ProfileNotFoundError(Exception):
    pass


def create_profile(user_id: int, exam_code: str, goals: str | None = None,
                    experience_level: str | None = None) -> StudentProfile:
    exam = Exam.query.filter_by(code=exam_code).first()
    if exam is None:
        raise ValueError(f"unknown exam code: {exam_code}")

    existing = StudentProfile.query.filter_by(user_id=user_id, exam_id=exam.id).first()
    if existing is not None:
        return existing

    profile = StudentProfile(
        user_id=user_id, exam_id=exam.id, goals=goals, experience_level=experience_level
    )
    db.session.add(profile)
    db.session.commit()
    return profile


def get_profile(user_id: int, exam_code: str) -> StudentProfile:
    exam = Exam.query.filter_by(code=exam_code).first()
    if exam is None:
        raise ProfileNotFoundError(f"unknown exam code: {exam_code}")

    profile = StudentProfile.query.filter_by(user_id=user_id, exam_id=exam.id).first()
    if profile is None:
        raise ProfileNotFoundError(f"no profile for user {user_id} on exam {exam_code}")
    return profile


def list_profiles(user_id: int) -> list[StudentProfile]:
    return StudentProfile.query.filter_by(user_id=user_id).all()


def profile_mastery_summary(profile: StudentProfile) -> dict[str, int]:
    return {record.topic.name: record.mastery_score for record in profile.mastery_records}


def profile_difficulty_summary(profile: StudentProfile) -> dict[str, int]:
    return {record.topic.name: record.current_difficulty for record in profile.mastery_records}


def profile_weaknesses(profile: StudentProfile) -> list[str]:
    open_mistakes = (
        Mistake.query.filter_by(student_profile_id=profile.id, resolution_status="open")
        .order_by(Mistake.frequency.desc())
        .all()
    )
    return [m.misconception for m in open_mistakes]


def _severity_for_frequency(frequency: int) -> str:
    if frequency >= 4:
        return "high"
    if frequency >= 2:
        return "medium"
    return "low"


def record_mistake(profile: StudentProfile, topic_id: int, misconception: str) -> Mistake:
    existing = Mistake.query.filter_by(
        student_profile_id=profile.id, topic_id=topic_id, misconception=misconception
    ).first()
    if existing is not None:
        existing.frequency += 1
        existing.severity = _severity_for_frequency(existing.frequency)
        db.session.commit()
        return existing

    mistake = Mistake(
        student_profile_id=profile.id, topic_id=topic_id, misconception=misconception,
        severity=_severity_for_frequency(1),
    )
    db.session.add(mistake)
    db.session.commit()
    return mistake


def recent_sessions(profile: StudentProfile, limit: int = 10) -> list[Session]:
    return (
        Session.query.filter_by(student_profile_id=profile.id)
        .order_by(Session.started_at.desc())
        .limit(limit)
        .all()
    )


def profile_progress_summary(profile: StudentProfile) -> dict:
    """A simple progress snapshot -- not an analytics dashboard (Section 8
    explicitly defers those past MVP), just enough for a student to see
    where they stand and what's next.
    """
    topics_total = Topic.query.filter_by(exam_id=profile.exam_id).count()
    mastery_records = profile.mastery_records

    overall_mastery = (
        round(sum(r.mastery_score for r in mastery_records) / len(mastery_records))
        if mastery_records else 0
    )
    weakest = min(mastery_records, key=lambda r: r.mastery_score) if mastery_records else None
    last_session = recent_sessions(profile, limit=1)

    next_topic, next_reason = select_next_topic(profile)

    return {
        "overall_mastery": overall_mastery,
        "topics_studied": len(mastery_records),
        "topics_total": topics_total,
        "weakest_topic": weakest.topic.name if weakest else None,
        "weakest_topic_mastery": weakest.mastery_score if weakest else None,
        "open_mistakes": len(profile_weaknesses(profile)),
        "last_session_at": last_session[0].started_at.isoformat() if last_session else None,
        "next_recommended_topic": next_topic.name,
        "next_recommended_reason": next_reason,
    }
