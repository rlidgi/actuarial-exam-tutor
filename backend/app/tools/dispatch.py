"""
Dispatches OpenAI tool calls to backend services.

Every handler takes validated args plus a ToolContext bound server-side to
the authenticated student -- the LLM never supplies student_profile_id
itself (see app/tools/schemas.py).
"""

from dataclasses import dataclass

from app.extensions import db
from app.models.exam import Topic
from app.models.session import Session
from app.models.student import StudentProfile
from app.services import curriculum_service, mastery_service, practice_service, rag_service
from app.services import student_service
from app.tools import schemas


@dataclass
class ToolContext:
    student_profile: StudentProfile
    session: Session


def _get_topic(exam_id: int, topic_name: str) -> Topic:
    topic = Topic.query.filter_by(exam_id=exam_id, name=topic_name).first()
    if topic is None:
        raise ValueError(f"unknown topic '{topic_name}' for this exam")
    return topic


def retrieve_textbook(args: dict, ctx: ToolContext) -> dict:
    parsed = schemas.RetrieveTextbookInput(**args, exam_code=ctx.student_profile.exam.code)
    chunks = rag_service.retrieve(
        query=f"{parsed.topic} {' '.join(parsed.keywords)}".strip(),
        exam_code=parsed.exam_code,
    )
    output = schemas.RetrieveTextbookOutput(
        sources=[
            schemas.TextbookSource(
                chapter=f"Chapter {c.chapter_number}",
                section=c.chapter_title,
                content=c.content,
                citation=c.citation,
            )
            for c in chunks
        ]
    )
    return output.model_dump()


def get_student_profile(args: dict, ctx: ToolContext) -> dict:
    profile = ctx.student_profile
    output = schemas.GetStudentProfileOutput(
        exam=profile.exam.code,
        current_topic=None,
        mastery=student_service.profile_mastery_summary(profile),
        weaknesses=student_service.profile_weaknesses(profile),
    )
    return output.model_dump()


def get_learning_history(args: dict, ctx: ToolContext) -> dict:
    parsed = schemas.GetLearningHistoryInput(**args)
    sessions = student_service.recent_sessions(ctx.student_profile, limit=parsed.limit)
    output = schemas.GetLearningHistoryOutput(
        sessions=[
            schemas.SessionSummaryItem(
                date=s.started_at.isoformat() if s.started_at else "",
                topics_covered=[str(t) for t in (s.topics_covered or [])],
                summary=s.summary or "",
            )
            for s in sessions
        ]
    )
    return output.model_dump()


def generate_practice_problem(args: dict, ctx: ToolContext) -> dict:
    parsed = schemas.GeneratePracticeProblemInput(**args)
    weaknesses = student_service.profile_weaknesses(ctx.student_profile)
    output = practice_service.generate_practice_problem(
        topic=parsed.topic,
        difficulty=parsed.difficulty,
        problem_type=parsed.type,
        weaknesses=weaknesses,
    )
    return output.model_dump()


def update_mastery(args: dict, ctx: ToolContext) -> dict:
    parsed = schemas.UpdateMasteryInput(**args)
    topic = _get_topic(ctx.student_profile.exam_id, parsed.topic)
    record = mastery_service.record_mastery_assessment(
        ctx.student_profile, topic, confidence=parsed.confidence,
        recommended_change=parsed.recommended_change,
    )
    output = schemas.UpdateMasteryOutput(accepted=True, new_mastery=record.mastery_score)
    return output.model_dump()


def select_next_topic(args: dict, ctx: ToolContext) -> dict:
    topic, reason = curriculum_service.select_next_topic(ctx.student_profile)
    output = schemas.SelectNextTopicOutput(topic=topic.name, reason=reason)
    return output.model_dump()


def save_session_summary(args: dict, ctx: ToolContext) -> dict:
    parsed = schemas.SaveSessionSummaryInput(**args)

    ctx.session.summary = parsed.summary
    ctx.session.topics_covered = parsed.topics_covered
    ctx.session.recommendations = parsed.recommendations
    db.session.commit()

    for misconception in parsed.misconceptions:
        for topic_name in parsed.topics_covered:
            topic = Topic.query.filter_by(
                exam_id=ctx.student_profile.exam_id, name=topic_name
            ).first()
            if topic is not None:
                student_service.record_mistake(ctx.student_profile, topic.id, misconception)
                break

    output = schemas.SaveSessionSummaryOutput(session_id=ctx.session.id)
    return output.model_dump()


TOOL_HANDLERS = {
    "retrieve_textbook": retrieve_textbook,
    "get_student_profile": get_student_profile,
    "get_learning_history": get_learning_history,
    "generate_practice_problem": generate_practice_problem,
    "update_mastery": update_mastery,
    "select_next_topic": select_next_topic,
    "save_session_summary": save_session_summary,
}
