from unittest.mock import MagicMock, patch

from app.models import Exam, Session, StudentProfile, Topic, User
from app.tools import dispatch


def _make_ctx(db):
    user = User(email="student@example.com")
    user.set_password("secret123")
    exam = Exam(code="P", name="Exam P")
    db.session.add_all([user, exam])
    db.session.commit()

    topic = Topic(exam_id=exam.id, name="General Probability")
    db.session.add(topic)
    db.session.commit()

    profile = StudentProfile(user_id=user.id, exam_id=exam.id)
    db.session.add(profile)
    db.session.commit()

    session = Session(student_profile_id=profile.id)
    db.session.add(session)
    db.session.commit()

    return dispatch.ToolContext(student_profile=profile, session=session), topic


def test_get_student_profile_returns_exam_and_mastery(app, db):
    ctx, topic = _make_ctx(db)

    result = dispatch.get_student_profile({}, ctx)

    assert result["exam"] == "P"
    assert result["mastery"] == {}
    assert result["weaknesses"] == []


def test_update_mastery_applies_bucketed_change(app, db):
    ctx, topic = _make_ctx(db)

    result = dispatch.update_mastery(
        {
            "topic": "General Probability",
            "assessment": "solved independently",
            "confidence": 0.9,
            "recommended_change": 8,
        },
        ctx,
    )

    assert result["accepted"] is True
    assert result["new_mastery"] > 0


def test_update_mastery_unknown_topic_raises(app, db):
    ctx, topic = _make_ctx(db)

    try:
        dispatch.update_mastery(
            {
                "topic": "Not A Real Topic",
                "assessment": "x",
                "confidence": 0.5,
                "recommended_change": 1,
            },
            ctx,
        )
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_select_next_topic_returns_unstudied_topic(app, db):
    ctx, topic = _make_ctx(db)

    result = dispatch.select_next_topic({}, ctx)

    assert result["topic"] == "General Probability"
    assert "not been studied" in result["reason"]


def test_save_session_summary_persists_summary_and_mistakes(app, db):
    ctx, topic = _make_ctx(db)

    result = dispatch.save_session_summary(
        {
            "topics_covered": ["General Probability"],
            "summary": "Covered axioms of probability.",
            "misconceptions": ["Confuses independence with mutual exclusivity"],
            "recommendations": "Review Venn diagrams.",
        },
        ctx,
    )

    assert result["session_id"] == ctx.session.id
    assert ctx.session.summary == "Covered axioms of probability."
    from app.services.student_service import profile_weaknesses

    assert profile_weaknesses(ctx.student_profile) == [
        "Confuses independence with mutual exclusivity"
    ]


def test_retrieve_textbook_uses_rag_service(app, db):
    ctx, topic = _make_ctx(db)

    fake_chunk = MagicMock(
        chapter_number=2, chapter_title="Axioms of Probability",
        content="Some textbook content.", citation="Ross, Chapter 2",
    )
    with patch("app.tools.dispatch.rag_service.retrieve", return_value=[fake_chunk]) as mock_retrieve:
        result = dispatch.retrieve_textbook({"topic": "axioms", "keywords": ["sample space"]}, ctx)

    mock_retrieve.assert_called_once()
    assert mock_retrieve.call_args.kwargs["exam_code"] == "P"
    assert result["sources"][0]["citation"] == "Ross, Chapter 2"


def test_generate_practice_problem_uses_practice_service(app, db):
    ctx, topic = _make_ctx(db)

    fake_output = MagicMock()
    fake_output.model_dump.return_value = {
        "problem_id": "abc",
        "prompt": "Compute P(A|B)...",
        "expected_answer_type": "numeric",
        "tolerance": 0.01,
    }
    with patch(
        "app.tools.dispatch.practice_service.generate_practice_problem",
        return_value=fake_output,
    ) as mock_generate:
        result = dispatch.generate_practice_problem(
            {"topic": "General Probability", "difficulty": 5, "type": "exam_style"}, ctx
        )

    mock_generate.assert_called_once()
    assert result["prompt"] == "Compute P(A|B)..."
