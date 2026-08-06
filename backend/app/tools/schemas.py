"""
Pydantic I/O contracts for the tutor's tool calls, per docs/PHASE0_ARCHITECTURE.md Section 5.

These are data contracts only. The orchestrator that actually invokes the LLM
with these as OpenAI tool definitions, and dispatches the resulting calls to
app/services/, is Phase 2 work.

student_profile_id is intentionally absent from every input schema: it is
bound server-side from the authenticated session, never supplied by the LLM.
"""

from typing import Literal

from pydantic import BaseModel, Field


class RetrieveTextbookInput(BaseModel):
    topic: str
    keywords: list[str] = Field(default_factory=list)
    exam_code: str


class TextbookSource(BaseModel):
    chapter: str
    section: str
    content: str
    citation: str


class RetrieveTextbookOutput(BaseModel):
    sources: list[TextbookSource]


class GetStudentProfileOutput(BaseModel):
    exam: str
    current_topic: str | None
    mastery: dict[str, int]
    weaknesses: list[str]


class GetLearningHistoryInput(BaseModel):
    limit: int = 10


class SessionSummaryItem(BaseModel):
    date: str
    topics_covered: list[str]
    summary: str


class GetLearningHistoryOutput(BaseModel):
    sessions: list[SessionSummaryItem]


class GeneratePracticeProblemInput(BaseModel):
    topic: str
    difficulty: int = Field(ge=1, le=10)
    type: Literal["exam_style", "conceptual", "drill"]


class GeneratePracticeProblemOutput(BaseModel):
    problem_id: str
    prompt: str
    expected_answer_type: Literal["numeric", "symbolic", "free_response"]
    tolerance: float | None = None


class UpdateMasteryInput(BaseModel):
    topic: str
    assessment: str
    confidence: float = Field(ge=0, le=1)
    recommended_change: int


class UpdateMasteryOutput(BaseModel):
    accepted: bool
    new_mastery: int


class SelectNextTopicOutput(BaseModel):
    topic: str
    reason: str


class SaveSessionSummaryInput(BaseModel):
    topics_covered: list[str]
    summary: str
    misconceptions: list[str] = Field(default_factory=list)
    recommendations: str


class SaveSessionSummaryOutput(BaseModel):
    session_id: int
