"""
OpenAI tool-calling definitions for the 7 tutor tools.

These are hand-written subsets of the schemas in app/tools/schemas.py:
fields that are bound server-side (student_profile_id, exam_code) are never
exposed to the model as parameters it can fill in.
"""

OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
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
    },
    {
        "type": "function",
        "function": {
            "name": "get_student_profile",
            "description": "Retrieve the current student's exam, mastery by topic, and known weaknesses.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_learning_history",
            "description": "Retrieve the student's previous session summaries.",
            "parameters": {
                "type": "object",
                "properties": {"limit": {"type": "integer", "default": 10}},
            },
        },
    },
    {
        "type": "function",
        "function": {
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
    },
    {
        "type": "function",
        "function": {
            "name": "update_mastery",
            "description": (
                "Report a mastery assessment after the student engages with a topic. "
                "The backend computes the actual mastery change; recommended_change is advisory."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "assessment": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "recommended_change": {"type": "integer"},
                },
                "required": ["topic", "assessment", "confidence", "recommended_change"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "select_next_topic",
            "description": "Ask the backend what topic the student should study next.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_session_summary",
            "description": "Persist a summary of this session. Call at the end of a session, not after every message.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topics_covered": {"type": "array", "items": {"type": "string"}},
                    "summary": {"type": "string"},
                    "misconceptions": {"type": "array", "items": {"type": "string"}},
                    "recommendations": {"type": "string"},
                },
                "required": ["topics_covered", "summary", "recommendations"],
            },
        },
    },
]
