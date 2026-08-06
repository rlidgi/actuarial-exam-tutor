"""
Exam P corpus configuration.

Chapter page ranges are PDF page indices (1-based), derived from each book's
printed-page numbering plus a fixed front-matter offset verified against the
actual source files:
  Ross      pdf_page = printed_page + 15
  Wackerly  pdf_page = printed_page + 24
  Hogg      pdf_page = printed_page + 16

Topic tags are one of the three official SOA Exam P syllabus topics:
General Probability, Univariate Random Variables, Multivariate Random
Variables. Tagging is chapter-level, not section-level -- retrieval relies
primarily on embedding similarity, so a coarse tag is sufficient to scope
results by topic without hand-mapping every subsection.

Hogg (Introduction to Mathematical Statistics, Hogg/McKean/Craig) is NOT the
book the official syllabus suggests (Probability and Statistical Inference,
Hogg/Tanis/Zimmerman) -- different book, same author surname. Only chapters
1-3 are ingested here: chapters 4-5 (statistical inference, consistency and
limiting distributions) are outside Exam P's syllabus, which does not test
estimation or asymptotic theory.
"""

from dataclasses import dataclass

GENERAL_PROBABILITY = "General Probability"
UNIVARIATE_RANDOM_VARIABLES = "Univariate Random Variables"
MULTIVARIATE_RANDOM_VARIABLES = "Multivariate Random Variables"


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


ROSS = BookSource(
    key="ross",
    title="A First Course in Probability",
    file_name="A-First-Course-in-Probability-8th-Edition.pdf",
    chapters=(
        Chapter(1, "Combinatorial Analysis", 16, 36, GENERAL_PROBABILITY),
        Chapter(2, "Axioms of Probability", 37, 72, GENERAL_PROBABILITY),
        Chapter(3, "Conditional Probability and Independence", 73, 131, GENERAL_PROBABILITY),
        Chapter(4, "Random Variables", 132, 200, UNIVARIATE_RANDOM_VARIABLES),
        Chapter(5, "Continuous Random Variables", 201, 246, UNIVARIATE_RANDOM_VARIABLES),
        Chapter(6, "Jointly Distributed Random Variables", 247, 311, MULTIVARIATE_RANDOM_VARIABLES),
        Chapter(7, "Properties of Expectation", 312, 402, MULTIVARIATE_RANDOM_VARIABLES),
        Chapter(8, "Limit Theorems", 403, 431, MULTIVARIATE_RANDOM_VARIABLES),
    ),
)

WACKERLY = BookSource(
    key="wackerly",
    title="Mathematical Statistics with Applications",
    file_name="Mathematical Statistics - 7th Edition - Wackerly.pdf",
    chapters=(
        Chapter(1, "What Is Statistics?", 25, 43, GENERAL_PROBABILITY),
        Chapter(2, "Probability", 44, 109, GENERAL_PROBABILITY),
        Chapter(3, "Discrete Random Variables and Their Probability Distributions", 110, 180, UNIVARIATE_RANDOM_VARIABLES),
        Chapter(4, "Continuous Variables and Their Probability Distributions", 181, 246, UNIVARIATE_RANDOM_VARIABLES),
        Chapter(5, "Multivariate Probability Distributions", 247, 319, MULTIVARIATE_RANDOM_VARIABLES),
        Chapter(6, "Functions of Random Variables", 320, 369, MULTIVARIATE_RANDOM_VARIABLES),
        Chapter(7, "Sampling Distributions and the Central Limit Theorem", 370, 413, MULTIVARIATE_RANDOM_VARIABLES),
    ),
)

HOGG = BookSource(
    key="hogg",
    title="Introduction to Mathematical Statistics",
    file_name="Introduction to Mathematical Statistics - 8th Edition - Hogg.pdf",
    chapters=(
        Chapter(1, "Probability and Distributions", 17, 100, GENERAL_PROBABILITY),
        Chapter(2, "Multivariate Distributions", 101, 170, MULTIVARIATE_RANDOM_VARIABLES),
        Chapter(3, "Some Special Distributions", 171, 240, UNIVARIATE_RANDOM_VARIABLES),
    ),
)

EXAM_P_SOURCES: tuple[BookSource, ...] = (ROSS, WACKERLY, HOGG)
