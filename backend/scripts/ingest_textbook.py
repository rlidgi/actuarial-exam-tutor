"""
Offline ingestion of the Exam P corpus into textbook_chunks.

Usage (from backend/, with the venv active and .env populated):
    python scripts/ingest_textbook.py [--corpus-dir PATH]

Extracts the configured chapters from app/rag/sources.py, chunks them,
embeds each chunk via OpenAI, and upserts them into Postgres/pgvector.
Existing chunks for Exam P are cleared and replaced on each run, so it's
safe to re-run after editing sources.py.
"""

import argparse
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND_DIR / ".env")

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models.exam import Exam, Topic  # noqa: E402
from app.models.textbook_chunk import TextbookChunk  # noqa: E402
from app.rag.chunk import chunk_book  # noqa: E402
from app.rag.extract import extract_book  # noqa: E402
from app.rag.sources import (  # noqa: E402
    EXAM_P_SOURCES,
    EXAM_P_TOPIC_WEIGHTS,
    GENERAL_PROBABILITY,
    MULTIVARIATE_RANDOM_VARIABLES,
    UNIVARIATE_RANDOM_VARIABLES,
)
from app.services.rag_service import embed_texts  # noqa: E402

EXAM_P_TOPICS = [GENERAL_PROBABILITY, UNIVARIATE_RANDOM_VARIABLES, MULTIVARIATE_RANDOM_VARIABLES]

EMBED_BATCH_SIZE = 100


def ensure_exam_and_topics() -> tuple[Exam, dict[str, Topic]]:
    exam = Exam.query.filter_by(code="P").first()
    if exam is None:
        exam = Exam(code="P", name="Exam P - Probability")
        db.session.add(exam)
        db.session.commit()

    topics: dict[str, Topic] = {}
    for name in EXAM_P_TOPICS:
        topic = Topic.query.filter_by(exam_id=exam.id, name=name).first()
        if topic is None:
            topic = Topic(exam_id=exam.id, name=name, exam_weight=EXAM_P_TOPIC_WEIGHTS[name])
            db.session.add(topic)
            db.session.commit()
        elif topic.exam_weight is None:
            topic.exam_weight = EXAM_P_TOPIC_WEIGHTS[name]
            db.session.commit()
        topics[name] = topic

    return exam, topics


def ingest(corpus_dir: Path) -> None:
    exam, topics = ensure_exam_and_topics()

    deleted = TextbookChunk.query.filter_by(exam_id=exam.id).delete()
    db.session.commit()
    if deleted:
        print(f"cleared {deleted} existing chunks for exam {exam.code}")

    for book in EXAM_P_SOURCES:
        print(f"extracting {book.key} ...")
        chapter_texts = extract_book(corpus_dir, book)
        text_chunks = chunk_book(book, chapter_texts)
        print(f"  {len(text_chunks)} chunks")

        for batch_start in range(0, len(text_chunks), EMBED_BATCH_SIZE):
            batch = text_chunks[batch_start : batch_start + EMBED_BATCH_SIZE]
            embeddings = embed_texts([c.content for c in batch])

            for text_chunk, embedding in zip(batch, embeddings):
                db.session.add(
                    TextbookChunk(
                        exam_id=exam.id,
                        topic_id=topics[text_chunk.topic].id,
                        book_key=text_chunk.book_key,
                        book_title=text_chunk.book_title,
                        chapter_number=text_chunk.chapter_number,
                        chapter_title=text_chunk.chapter_title,
                        citation=text_chunk.citation,
                        content=text_chunk.content,
                        embedding=embedding,
                    )
                )
            db.session.commit()
            print(f"  embedded+stored {min(batch_start + EMBED_BATCH_SIZE, len(text_chunks))}/{len(text_chunks)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--corpus-dir", type=Path, default=BACKEND_DIR.parent / "folder",
        help="directory containing the source textbook PDFs",
    )
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        ingest(args.corpus_dir)


if __name__ == "__main__":
    main()
