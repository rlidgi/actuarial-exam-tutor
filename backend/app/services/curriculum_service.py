from app.models.exam import Topic
from app.models.mastery import Mastery
from app.models.student import StudentProfile
from app.services.mastery_service import decay_for

DEFAULT_EXAM_WEIGHT = 100.0 / 3  # even split if a topic has no configured weight


def select_next_topic(student_profile: StudentProfile) -> tuple[Topic, str]:
    """Picks the exam topic the student most needs to review next.

    Unstudied topics are prioritized by syllabus weight (cover the
    heavier-weighted material first). Among studied topics, priority is
    (100 - decayed_mastery) * weight -- a topic that's both weak and
    heavily-weighted on the exam outranks one that's merely weak. Decay
    accounts for forgetting since last review (Section 25), so a
    previously-strong but long-untouched topic can resurface even with a
    high recorded score. Full prerequisite-graph awareness stays deferred
    per the spec's MVP scope.
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
        topic = max(unstudied, key=lambda t: t.exam_weight or DEFAULT_EXAM_WEIGHT)
        weight = topic.exam_weight or DEFAULT_EXAM_WEIGHT
        return topic, f"{topic.name} has not been studied yet and carries {weight:.0f}% exam weight."

    def priority(topic: Topic) -> float:
        record = mastery_by_topic[topic.id]
        decay = decay_for(record.last_reviewed_at) if record.last_reviewed_at else 0
        decayed_mastery = max(0, record.mastery_score - decay)
        weight = topic.exam_weight or DEFAULT_EXAM_WEIGHT
        return (100 - decayed_mastery) * weight

    best_topic = max(topics, key=priority)
    record = mastery_by_topic[best_topic.id]
    decay = decay_for(record.last_reviewed_at) if record.last_reviewed_at else 0
    weight = best_topic.exam_weight or DEFAULT_EXAM_WEIGHT

    if decay > 0:
        reason = (
            f"{best_topic.name} was last at {record.mastery_score}% but hasn't been reviewed "
            f"in a while (estimated {decay:.0f} points of decay), and carries {weight:.0f}% exam weight."
        )
    else:
        reason = (
            f"{best_topic.name} has the lowest effective mastery ({record.mastery_score}%) "
            f"weighted by its {weight:.0f}% exam weight."
        )
    return best_topic, reason
