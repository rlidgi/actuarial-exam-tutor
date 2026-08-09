"""
Offline ingestion of an exam's corpus into textbook_chunks.

Usage (from backend/, with the venv active and .env populated):
    python scripts/ingest_textbook.py [--exam CODE] [--corpus-dir PATH]

Extracts the configured chapters from app/rag/sources_<exam>.py, chunks
them, embeds each chunk via OpenAI, and upserts them into Postgres/pgvector.
Existing chunks for the exam are cleared and replaced on each run, so it's
safe to re-run after editing that exam's sources module. --corpus-dir
defaults to <repo_root>/<exam code lowercased> (e.g. p/, fm/, fam/).
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
from app.rag.exam_sources import sources_for, topic_names_for, topic_weights_for  # noqa: E402
from app.rag.extract import extract_book  # noqa: E402
from app.services.rag_service import embed_texts  # noqa: E402

EMBED_BATCH_SIZE = 100

EXAM_NAMES = {
    "P": "Exam P - Probability",
    "FM": "Exam FM - Financial Mathematics",
    "FAM": "Exam FAM - Fundamentals of Actuarial Mathematics",
}


def ensure_exam_and_topics(exam_code: str) -> tuple[Exam, dict[str, Topic]]:
    exam = Exam.query.filter_by(code=exam_code).first()
    if exam is None:
        exam = Exam(code=exam_code, name=EXAM_NAMES.get(exam_code, f"Exam {exam_code}"))
        db.session.add(exam)
        db.session.commit()

    topic_weights = topic_weights_for(exam_code)
    topics: dict[str, Topic] = {}
    for name in topic_names_for(exam_code):
        topic = Topic.query.filter_by(exam_id=exam.id, name=name).first()
        if topic is None:
            topic = Topic(exam_id=exam.id, name=name, exam_weight=topic_weights[name])
            db.session.add(topic)
            db.session.commit()
        elif topic.exam_weight is None:
            topic.exam_weight = topic_weights[name]
            db.session.commit()
        topics[name] = topic

    return exam, topics


def ingest(exam_code: str, corpus_dir: Path) -> None:
    exam, topics = ensure_exam_and_topics(exam_code)

    deleted = TextbookChunk.query.filter_by(exam_id=exam.id).delete()
    db.session.commit()
    if deleted:
        print(f"cleared {deleted} existing chunks for exam {exam.code}")

    for book in sources_for(exam_code):
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
    parser.add_argument("--exam", default="P", help="exam code, e.g. P, FM, FAM")
    parser.add_argument(
        "--corpus-dir", type=Path, default=None,
        help="directory containing the source textbook PDFs (default: <repo_root>/<exam code lowercased>)",
    )
    args = parser.parse_args()
    exam_code = args.exam.upper()
    corpus_dir = args.corpus_dir or (BACKEND_DIR.parent / exam_code.lower())

    app = create_app()
    with app.app_context():
        ingest(exam_code, corpus_dir)


if __name__ == "__main__":
    main()
