"""
OpenAI tool-calling definitions for the 7 tutor tools, in the Responses API
shape (flat -- {"type": "function", "name": ..., ...}, not the Chat
Completions shape nested under a "function" key).

These are hand-written subsets of the schemas in app/tools/schemas.py:
fields that are bound server-side (student_profile_id, exam_code) are never
exposed to the model as parameters it can fill in.

The `topic` parameter is constrained to the exact leaf (learning-outcome)
topic names via enum wherever dispatch.py does an exact-match Topic lookup
on it (update_mastery, save_session_summary) -- otherwise the model invents
natural-sounding subtopic names that don't match any row and the call fails
or silently no-ops. Free text is left alone for
retrieve_textbook/generate_practice_problem, which use `topic` as
search/prompt content rather than a lookup key, and are more useful for it.
This enum is Exam-P-specific; if a second exam is added this needs to
become dynamic per exam.
"""

from app.exam_p_syllabus import LEARNING_OUTCOME_NAMES

TOPIC_ENUM = LEARNING_OUTCOME_NAMES

OPENAI_TOOLS = [
    {
        "type": "function",
        "name": "retrieve_textbook",
        "description": (
            "Retrieve authoritative textbook excerpts. Use when textbook-specific "
            "wording, a formula, or a citation is needed -- not for every message."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string"},
                "keywords": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["topic"],
        },
    },
    {
        "type": "function",
        "name": "get_student_profile",
        "description": "Retrieve the current student's exam, mastery by topic, and known weaknesses.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "type": "function",
        "name": "get_learning_history",
        "description": "Retrieve the student's previous session summaries.",
        "parameters": {
            "type": "object",
            "properties": {"limit": {"type": "integer", "default": 10}},
        },
    },
    {
        "type": "function",
        "name": "generate_practice_problem",
        "description": "Generate one exam-style practice problem targeted at the student's level and weaknesses.",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string"},
                "difficulty": {"type": "integer", "minimum": 1, "maximum": 10},
                "type": {
                    "type": "string",
                    "enum": ["exam_style", "conceptual", "drill"],
                },
            },
            "required": ["topic", "difficulty", "type"],
        },
    },
    {
        "type": "function",
        "name": "update_mastery",
        "description": (
            "Report a mastery assessment after the student engages with a topic. "
            "The backend computes the actual mastery change; recommended_change is advisory."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "enum": TOPIC_ENUM},
                "assessment": {"type": "string"},
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": (
                        "How confident you are that the student's demonstrated understanding is "
                        "genuine -- reasoned through, not guessed, memorized, or lifted from a hint "
                        "you just gave. Not your confidence in your own diagnosis, and not how "
                        "confident the student sounded. 0 = they got there by guessing or reciting a "
                        "memorized step with no real grasp; 1 = they clearly reasoned it through "
                        "themselves and could explain why."
                    ),
                },
                "recommended_change": {"type": "integer"},
            },
            "required": ["topic", "assessment", "confidence", "recommended_change"],
        },
    },
    {
        "type": "function",
        "name": "select_next_topic",
        "description": "Ask the backend what topic the student should study next.",
        "parameters": {"type": "object", "properties": {}},
    },
    {
        "type": "function",
        "name": "save_session_summary",
        "description": "Persist a summary of this session. Call at the end of a session, not after every message.",
        "parameters": {
            "type": "object",
            "properties": {
                "topics_covered": {
                    "type": "array",
                    "items": {"type": "string", "enum": TOPIC_ENUM},
                },
                "summary": {"type": "string"},
                "misconceptions": {"type": "array", "items": {"type": "string"}},
                "recommendations": {"type": "string"},
            },
            "required": ["topics_covered", "summary", "recommendations"],
        },
    },
]
