from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector

from app.extensions import db

EMBEDDING_DIMENSIONS = 1536  # OpenAI text-embedding-3-small


class TextbookChunk(db.Model):
    __tablename__ = "textbook_chunks"

    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey("exams.id"), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey("topics.id"), nullable=True)

    book_key = db.Column(db.String(64), nullable=False)
    book_title = db.Column(db.String(255), nullable=False)
    chapter_number = db.Column(db.Integer, nullable=False)
    chapter_title = db.Column(db.String(255), nullable=False)
    citation = db.Column(db.String(512), nullable=False)

    content = db.Column(db.Text, nullable=False)
    embedding = db.Column(Vector(EMBEDDING_DIMENSIONS), nullable=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    exam = db.relationship("Exam")
    topic = db.relationship("Topic")
