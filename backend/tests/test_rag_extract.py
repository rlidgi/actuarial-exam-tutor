from pathlib import Path

import pytest

from app.rag.extract import extract_book, extract_chapter_text
from app.rag.sources import EXAM_P_SOURCES, ROSS

CORPUS_DIR = Path(__file__).resolve().parents[2] / "folder"

pytestmark = pytest.mark.skipif(
    not CORPUS_DIR.exists(), reason="textbook corpus not present on this machine"
)


def test_extract_ross_chapter_1_mentions_combinatorics():
    text = extract_chapter_text(CORPUS_DIR / ROSS.file_name, ROSS.chapters[0])
    assert "permutation" in text.lower() or "combinatorial" in text.lower()


def test_extract_book_returns_all_chapters():
    chapters = extract_book(CORPUS_DIR, ROSS)
    assert set(chapters.keys()) == {c.number for c in ROSS.chapters}
    for text in chapters.values():
        assert len(text) > 500


@pytest.mark.parametrize("book", EXAM_P_SOURCES, ids=lambda b: b.key)
def test_extract_each_source_book(book):
    chapters = extract_book(CORPUS_DIR, book)
    for chapter in book.chapters:
        assert len(chapters[chapter.number]) > 500, (
            f"{book.key} chapter {chapter.number} extracted suspiciously little text"
        )
