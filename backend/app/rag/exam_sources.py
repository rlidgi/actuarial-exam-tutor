"""Registry mapping an exam code to its textbook corpus config module.

Lets scripts/ingest_textbook.py look up an exam's BookSources by code
instead of hardcoding an import -- add a new exam by writing sources_<code>.py
(matching sources_p.py's shape: SOURCES, TOPIC_WEIGHTS, TOPIC_NAMES) and
registering it here.
"""

from app.rag import sources_fm, sources_p

SOURCE_MODULES = {
    "P": sources_p,
    "FM": sources_fm,
}


def sources_for(exam_code: str):
    return SOURCE_MODULES[exam_code.upper()].SOURCES


def topic_weights_for(exam_code: str) -> dict[str, float]:
    return SOURCE_MODULES[exam_code.upper()].TOPIC_WEIGHTS


def topic_names_for(exam_code: str) -> list[str]:
    return SOURCE_MODULES[exam_code.upper()].TOPIC_NAMES
