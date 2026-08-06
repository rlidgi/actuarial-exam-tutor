from app.models.exam import Topic
from app.models.mastery import Mastery
from app.models.student import StudentProfile


def select_next_topic(student_profile: StudentProfile) -> tuple[Topic, str]:
    """Picks the exam topic the student most needs to review next.

    First-pass heuristic: prioritize topics with no mastery record yet (never
    studied), then the lowest-scoring recorded topic. Prerequisite-awareness
    and review-timing are deferred to Phase 3 per docs/PHASE0_ARCHITECTURE.md.
    """
    topics = Topic.query.filter_by(exam_id=student_profile.exam_id).all()
    if not topics:
        raise ValueError(f"exam {student_profile.exam_id} has no topics configured")

    mastery_by_topic = {
        record.topic_id: record
        for record in Mastery.query.filter_by(student_profile_id=student_profile.id).all()
    }

    unstudied = [t for t in topics if t.id not in mastery_by_topic]
    if unstudied:
        topic = unstudied[0]
        return topic, f"{topic.name} has not been studied yet."

    weakest_topic, weakest_record = min(
        ((t, mastery_by_topic[t.id]) for t in topics),
        key=lambda pair: pair[1].mastery_score,
    )
    return (
        weakest_topic,
        f"{weakest_topic.name} has the lowest mastery ({weakest_record.mastery_score}%).",
    )
