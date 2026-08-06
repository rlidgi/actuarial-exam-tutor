from pathlib import Path

from pypdf import PdfReader

from app.rag.sources import BookSource, Chapter


def extract_chapter_text(pdf_path: Path, chapter: Chapter) -> str:
    reader = PdfReader(str(pdf_path))
    pages = reader.pages[chapter.pdf_start - 1 : chapter.pdf_end]
    return "\n\n".join(page.extract_text() or "" for page in pages)


def extract_book(corpus_dir: Path, book: BookSource) -> dict[int, str]:
    pdf_path = corpus_dir / book.file_name
    if not pdf_path.exists():
        raise FileNotFoundError(f"expected textbook at {pdf_path}")

    return {
        chapter.number: extract_chapter_text(pdf_path, chapter) for chapter in book.chapters
    }
