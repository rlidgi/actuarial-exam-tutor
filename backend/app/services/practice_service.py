"""
Generates practice problems for the generate_practice_problem tool.

Problem authoring is inherently a content-generation task, not a lookup, so
this makes its own structured OpenAI call rather than trying to template
problems by hand. Kept as a separate call from tutor_service's main
conversational turn so problem generation and teaching dialogue can use
different models independently -- currently both are pinned to gpt-5.6-sol
(quality prioritized over Section 48's cost-tiering suggestion here).
"""

import json
import uuid

from flask import current_app
from openai import OpenAI

from app.tools.schemas import GeneratePracticeProblemOutput

PROBLEM_MODEL = "gpt-5.6-sol"

SYSTEM_PROMPT = (
    "You write SOA Exam P style probability practice problems. Given a topic, "
    "difficulty (1-10), a problem type, and the student's known weaknesses, "
    "write one problem. Respond with JSON matching exactly this shape: "
    '{"prompt": string, "expected_answer_type": "numeric" | "symbolic" | "free_response", '
    '"tolerance": number or null}. "tolerance" is only meaningful when '
    'expected_answer_type is "numeric" (acceptable absolute error on the final '
    "answer); use null otherwise. Do not include the answer or solution."
)


def _client() -> OpenAI:
    return OpenAI(api_key=current_app.config["OPENAI_API_KEY"])


def generate_practice_problem(
    topic: str, difficulty: int, problem_type: str, weaknesses: list[str]
) -> GeneratePracticeProblemOutput:
    weakness_text = "; ".join(weaknesses) if weaknesses else "none recorded"
    user_prompt = (
        f"Topic: {topic}\nDifficulty: {difficulty}/10\nType: {problem_type}\n"
        f"Student's known weaknesses: {weakness_text}"
    )

    response = _client().chat.completions.create(
        model=PROBLEM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )

    body = json.loads(response.choices[0].message.content)
    return GeneratePracticeProblemOutput(
        problem_id=str(uuid.uuid4()),
        prompt=body["prompt"],
        expected_answer_type=body["expected_answer_type"],
        tolerance=body.get("tolerance"),
    )
