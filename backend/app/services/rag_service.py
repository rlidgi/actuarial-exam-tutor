"""
Retrieval for the tutor's retrieve_textbook tool.

Indexing (chunking, embedding, storing) is a separate offline concern --
see backend/scripts/ingest_textbook.py. This module only handles turning a
query into an embedding and finding the nearest textbook_chunks rows.
"""

from flask import current_app
from openai import OpenAI

from app.extensions import db
from app.models.exam import Exam
from app.models.textbook_chunk import TextbookChunk

EMBEDDING_MODEL = "text-embedding-3-small"


def _client() -> OpenAI:
    return OpenAI(api_key=current_app.config["OPENAI_API_KEY"])


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    response = _client().embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]


def embed_query(query: str) -> list[float]:
    return embed_texts([query])[0]


def retrieve(query: str, exam_code: str, top_k: int = 5) -> list[TextbookChunk]:
    exam = Exam.query.filter_by(code=exam_code).first()
    if exam is None:
        return []

    query_embedding = embed_query(query)

    return (
        TextbookChunk.query.filter_by(exam_id=exam.id)
        .order_by(TextbookChunk.embedding.cosine_distance(query_embedding))
        .limit(top_k)
        .all()
    )
