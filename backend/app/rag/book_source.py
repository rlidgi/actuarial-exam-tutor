"""Exam-agnostic textbook corpus config shapes.

Kept separate from any per-exam sources module (sources_p.py, sources_fm.py,
...) so app/rag/extract.py and app/rag/chunk.py -- which operate generically
on any BookSource/Chapter regardless of which exam it belongs to -- don't
depend on one specific exam's config file.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Chapter:
    number: int
    title: str
    pdf_start: int
    pdf_end: int  # inclusive
    topic: str


@dataclass(frozen=True)
class BookSource:
    key: str
    title: str
    file_name: str
    chapters: tuple[Chapter, ...]
