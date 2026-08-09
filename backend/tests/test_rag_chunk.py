from app.rag.book_source import BookSource, Chapter
from app.rag.chunk import chunk_book, chunk_chapter_text
from app.rag.sources_p import GENERAL_PROBABILITY


def _book(chapters):
    return BookSource(key="test", title="Test Book", file_name="test.pdf", chapters=chapters)


def test_chunk_chapter_text_splits_on_word_count():
    chapter = Chapter(1, "Intro", 1, 1, GENERAL_PROBABILITY)
    book = _book((chapter,))
    text = " ".join(f"word{i}" for i in range(1000))

    chunks = chunk_chapter_text(book, chapter, text, chunk_size_words=350, overlap_words=50)

    assert len(chunks) > 1
    for c in chunks:
        assert c.topic == GENERAL_PROBABILITY
        assert c.book_key == "test"
        assert "Chapter 1" in c.citation


def test_chunk_chapter_text_overlap_repeats_words():
    chapter = Chapter(1, "Intro", 1, 1, GENERAL_PROBABILITY)
    book = _book((chapter,))
    text = " ".join(f"word{i}" for i in range(500))

    chunks = chunk_chapter_text(book, chapter, text, chunk_size_words=350, overlap_words=50)

    first_words = chunks[0].content.split()
    second_words = chunks[1].content.split()
    assert first_words[-50:] == second_words[:50]


def test_chunk_chapter_text_empty_text_returns_no_chunks():
    chapter = Chapter(1, "Intro", 1, 1, GENERAL_PROBABILITY)
    book = _book((chapter,))

    assert chunk_chapter_text(book, chapter, "") == []


def test_chunk_book_covers_all_chapters():
    ch1 = Chapter(1, "One", 1, 1, GENERAL_PROBABILITY)
    ch2 = Chapter(2, "Two", 2, 2, GENERAL_PROBABILITY)
    book = _book((ch1, ch2))

    chunks = chunk_book(
        book,
        {1: " ".join(f"a{i}" for i in range(400)), 2: " ".join(f"b{i}" for i in range(400))},
    )

    chapter_numbers = {c.chapter_number for c in chunks}
    assert chapter_numbers == {1, 2}
