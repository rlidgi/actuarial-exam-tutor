"""
Seeds the 22 granular learning-outcome topics under Exam P's 3 syllabus
sections, and resets any Mastery/Mistake data recorded against the 3
broad sections directly (those become organizational parents only --
mastery is tracked at the leaf/learning-outcome level from here on).

Usage (from backend/, with the venv active and .env populated):
    python scripts/seed_p_learning_outcomes.py

Idempotent: safe to re-run. Existing leaf topics are left as-is (their
Mastery data is NOT touched by re-running this); only the initial reset of
parent-level Mastery/Mistake rows happens, and only for rows that still
point at a parent (category) topic.
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND_DIR / ".env")

from app import create_app  # noqa: E402
from app.exam_p_syllabus import ALL_LEARNING_OUTCOMES, weight_for  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models.exam import Exam, Topic  # noqa: E402
from app.models.mastery import Mastery  # noqa: E402
from app.models.mistake import Mistake  # noqa: E402


def seed() -> None:
    exam = Exam.query.filter_by(code="P").first()
    if exam is None:
        raise RuntimeError("Exam P not found -- run scripts/ingest_textbook.py first")

    parents = {t.name: t for t in Topic.query.filter_by(exam_id=exam.id, parent_topic_id=None).all()}
    print(f"found {len(parents)} parent (category) topics: {list(parents)}")

    reset_parent_ids = [t.id for t in parents.values()]
    deleted_mastery = Mastery.query.filter(Mastery.topic_id.in_(reset_parent_ids)).delete(
        synchronize_session=False
    )
    deleted_mistakes = Mistake.query.filter(Mistake.topic_id.in_(reset_parent_ids)).delete(
        synchronize_session=False
    )
    db.session.commit()
    if deleted_mastery or deleted_mistakes:
        print(f"reset {deleted_mastery} Mastery and {deleted_mistakes} Mistake rows tied to parent topics")

    created = 0
    for outcome in ALL_LEARNING_OUTCOMES:
        parent = parents.get(outcome.category)
        if parent is None:
            raise RuntimeError(f"parent category '{outcome.category}' not found -- seed it first")

        existing = Topic.query.filter_by(exam_id=exam.id, name=outcome.name).first()
        if existing is not None:
            continue

        db.session.add(
            Topic(
                exam_id=exam.id,
                name=outcome.name,
                description=outcome.description,
                exam_weight=weight_for(outcome),
                parent_topic_id=parent.id,
            )
        )
        created += 1
    db.session.commit()
    print(f"created {created} new leaf topics ({len(ALL_LEARNING_OUTCOMES) - created} already existed)")


def main() -> None:
    app = create_app()
    with app.app_context():
        seed()


if __name__ == "__main__":
    main()
