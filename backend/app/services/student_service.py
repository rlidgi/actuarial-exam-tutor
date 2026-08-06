from app.extensions import db
from app.models.exam import Exam
from app.models.mistake import Mistake
from app.models.session import Session
from app.models.student import StudentProfile


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


def profile_weaknesses(profile: StudentProfile) -> list[str]:
    open_mistakes = (
        Mistake.query.filter_by(student_profile_id=profile.id, resolution_status="open")
        .order_by(Mistake.frequency.desc())
        .all()
    )
    return [m.misconception for m in open_mistakes]


def record_mistake(profile: StudentProfile, topic_id: int, misconception: str) -> Mistake:
    existing = Mistake.query.filter_by(
        student_profile_id=profile.id, topic_id=topic_id, misconception=misconception
    ).first()
    if existing is not None:
        existing.frequency += 1
        db.session.commit()
        return existing

    mistake = Mistake(
        student_profile_id=profile.id, topic_id=topic_id, misconception=misconception
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
