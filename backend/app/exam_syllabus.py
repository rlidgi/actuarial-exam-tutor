"""Registry mapping an exam code to its syllabus learning-outcomes module.

Add a new exam by writing exam_syllabus_<code>.py (matching
exam_syllabus_p.py's shape: ALL_LEARNING_OUTCOMES, weight_for,
LEARNING_OUTCOME_NAMES) and registering it here. Used by
scripts/seed_learning_outcomes.py (topic seeding) and
tools/openai_tools.py (constraining the model's per-exam topic enum).
"""

from app import exam_syllabus_fam, exam_syllabus_fm, exam_syllabus_p

SYLLABUS_MODULES = {
    "P": exam_syllabus_p,
    "FM": exam_syllabus_fm,
    "FAM": exam_syllabus_fam,
}


def all_learning_outcomes_for(exam_code: str):
    return SYLLABUS_MODULES[exam_code.upper()].ALL_LEARNING_OUTCOMES


def weight_for(exam_code: str, outcome) -> float:
    return SYLLABUS_MODULES[exam_code.upper()].weight_for(outcome)


def learning_outcome_names_for(exam_code: str) -> list[str]:
    return SYLLABUS_MODULES[exam_code.upper()].LEARNING_OUTCOME_NAMES
