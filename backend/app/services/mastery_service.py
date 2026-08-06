"""
Owns the mastery-update formula described in docs/PHASE0_ARCHITECTURE.md.

The LLM never writes mastery_score directly. It reports an assessment via the
update_mastery tool; this module computes the actual delta. Constants are a
first-pass starting point for Phase 3 tuning, not calibrated pedagogy.
"""

from datetime import datetime, timezone
from enum import Enum

from app.extensions import db
from app.models.exam import Topic
from app.models.mastery import Mastery
from app.models.student import StudentProfile

DECAY_RATE_PER_DAY = 0.3
DECAY_GRACE_PERIOD_DAYS = 14
MAX_DECAY = 15


class PerformanceOutcome(str, Enum):
    CORRECT_INDEPENDENT = "correct_independent"
    CORRECT_WITH_ONE_HINT = "correct_with_one_hint"
    CORRECT_WITH_MULTIPLE_HINTS = "correct_with_multiple_hints"
    INCORRECT_NO_MISCONCEPTION = "incorrect_no_misconception"
    INCORRECT_WITH_MISCONCEPTION = "incorrect_with_misconception"


PERFORMANCE_ADJUSTMENT = {
    PerformanceOutcome.CORRECT_INDEPENDENT: 8,
    PerformanceOutcome.CORRECT_WITH_ONE_HINT: 3,
    PerformanceOutcome.CORRECT_WITH_MULTIPLE_HINTS: 1,
    PerformanceOutcome.INCORRECT_NO_MISCONCEPTION: -2,
    PerformanceOutcome.INCORRECT_WITH_MISCONCEPTION: -5,
}


def _clamp(value: float, low: float = 0, high: float = 100) -> int:
    return int(round(max(low, min(high, value))))


def confidence_adjustment(llm_confidence: float) -> float:
    return (llm_confidence - 0.5) * 4


def decay_for(last_reviewed_at: datetime, now: datetime | None = None) -> float:
    now = now or datetime.now(timezone.utc)
    if last_reviewed_at.tzinfo is None:
        # DB round-trips (notably SQLite) drop tzinfo from generic DateTime
        # columns; values are always written in UTC, so treat naive as UTC.
        last_reviewed_at = last_reviewed_at.replace(tzinfo=timezone.utc)
    days_since_review = (now - last_reviewed_at).days
    overdue_days = max(0, days_since_review - DECAY_GRACE_PERIOD_DAYS)
    return min(MAX_DECAY, DECAY_RATE_PER_DAY * overdue_days)


def apply_mastery_update(
    student_profile: StudentProfile,
    topic: Topic,
    outcome: PerformanceOutcome,
    llm_confidence: float,
) -> Mastery:
    record = Mastery.query.filter_by(
        student_profile_id=student_profile.id, topic_id=topic.id
    ).first()

    if record is None:
        record = Mastery(
            student_profile_id=student_profile.id, topic_id=topic.id, mastery_score=0
        )
        db.session.add(record)

    performance = PERFORMANCE_ADJUSTMENT[outcome]
    confidence_delta = confidence_adjustment(llm_confidence)
    decay = decay_for(record.last_reviewed_at or datetime.now(timezone.utc))

    record.mastery_score = _clamp(record.mastery_score + performance + confidence_delta - decay)
    record.confidence = llm_confidence
    record.last_reviewed_at = datetime.now(timezone.utc)

    db.session.commit()
    return record
