from dataclasses import dataclass

from app.rag.book_source import BookSource, Chapter

CHUNK_SIZE_WORDS = 350
CHUNK_OVERLAP_WORDS = 50


@dataclass(frozen=True)
class TextChunk:
    book_key: str
    book_title: str
    chapter_number: int
    chapter_title: str
    topic: str
    content: str
    citation: str


def chunk_chapter_text(
    book: BookSource, chapter: Chapter, text: str,
    chunk_size_words: int = CHUNK_SIZE_WORDS,
    overlap_words: int = CHUNK_OVERLAP_WORDS,
) -> list[TextChunk]:
    words = text.split()
    if not words:
        return []

    chunks: list[TextChunk] = []
    step = chunk_size_words - overlap_words
    for start in range(0, len(words), step):
        piece = words[start : start + chunk_size_words]
        if not piece:
            continue
        content = " ".join(piece)
        chunks.append(
            TextChunk(
                book_key=book.key,
                book_title=book.title,
                chapter_number=chapter.number,
                chapter_title=chapter.title,
                topic=chapter.topic,
                content=content,
                citation=f"{book.title}, Chapter {chapter.number} ({chapter.title})",
            )
        )
        if start + chunk_size_words >= len(words):
            break

    return chunks


def chunk_book(book: BookSource, chapter_texts: dict[int, str]) -> list[TextChunk]:
    chunks: list[TextChunk] = []
    for chapter in book.chapters:
        text = chapter_texts.get(chapter.number, "")
        chunks.extend(chunk_chapter_text(book, chapter, text))
    return chunks
