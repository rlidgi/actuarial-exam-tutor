# Actuarial Tutor AI Platform — Phase 0 Technical Plan

Status: draft, pending approval to begin Phase 1.
MVP scope: SOA Exam P. Architecture must support FM and FAM without rework.

## 1. Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Backend | Python + Flask | Blueprints per domain (chat, students, practice). Sync views; streaming via `Response` generator for chat. |
| ORM / migrations | Flask-SQLAlchemy + Flask-Migrate (Alembic) | |
| Validation / tool schemas | Pydantic | Used independently of any web framework — defines tool I/O contracts shared between the orchestrator and OpenAI tool-calling. |
| Database | PostgreSQL + pgvector | One database for relational student/curriculum data and textbook embeddings. Avoids a second piece of infra for MVP; migrate to a dedicated vector store later only if retrieval scale demands it. |
| LLM | OpenAI API, native function/tool calling | Thin custom orchestration loop in `services/tutor_service.py` — no LangChain/agent framework, per the spec's "don't move deterministic logic into the LLM" and "avoid unnecessary dependencies" rules. |
| Frontend | Next.js (TypeScript) + Tailwind | Chat UI + mastery dashboard. |
| Auth | JWT-based, in-house (Flask-JWT-Extended) | Deferred managed-auth decision; simple enough for MVP, swappable later. |
| Testing | pytest (backend), Vitest/RTL (frontend), small LLM-eval harness for Section 41 scenarios | |
| Deployment (MVP) | Docker Compose locally; single-region managed hosting later | Multi-region/scaling is explicitly Phase 5. |

## 2. Component Responsibilities (unchanged from spec, restated as modules)

- `api/` — HTTP boundary only. No business logic.
- `services/tutor_service.py` — the orchestrator. Assembles context, runs the OpenAI tool-calling loop, never touches the DB directly except through other services.
- `services/student_service.py` — student profile, mastery reads/writes, mistake tracking.
- `services/curriculum_service.py` — exam/topic/prerequisite data, `select_next_topic` logic.
- `services/mastery_service.py` — owns the mastery-update formula (Section 4 below). The LLM proposes an assessment; this service computes the actual delta.
- `services/rag_service.py` — chunk retrieval, exam-scoped filtering, citation formatting.
- `tools/` — one file per tool, each wrapping a service call and validating I/O against its Pydantic schema.

## 3. Data Model

Exam is a first-class table so P/FM/FAM share the same schema with no migration later.

```
Exam
  id, code ("P","FM","FAM"), name

Topic
  id, exam_id (FK), name, description
TopicPrerequisite
  topic_id (FK), prerequisite_topic_id (FK)

User
  id, email, password_hash, created_at

StudentProfile
  id, user_id (FK), exam_id (FK), goals, experience_level, created_at

Mastery
  id, student_profile_id (FK), topic_id (FK), mastery_score (0-100),
  confidence, last_reviewed_at

Mistake
  id, student_profile_id (FK), topic_id (FK), misconception (text),
  frequency, severity, resolution_status

Session
  id, student_profile_id (FK), started_at, ended_at, summary (text),
  topics_covered (topic_id[]), recommendations (text)

Message
  id, session_id (FK), role, content, created_at
  -- bounded short-term buffer only; pruned/summarized into Session.summary,
  -- not the system of record for long-term memory
```

A student can have one `StudentProfile` per exam, so a user studying P and later FM doesn't need a new account — just a new profile row.

## 4. Mastery Update Formula (first pass — tunable)

The LLM never writes `mastery_score`. It calls `update_mastery()` with an assessment; `mastery_service.py` computes:

```
new_mastery = clamp(current_mastery + performance_adjustment + confidence_adjustment - decay, 0, 100)
```

- `performance_adjustment` (from correctness + independence, as reported by the tool call):
  - correct, independent: +8
  - correct, after one hint: +3
  - correct, after multiple hints: +1
  - incorrect, no clear misconception: -2
  - incorrect, with identified misconception: -5
- `confidence_adjustment = (llm_confidence - 0.5) * 4` → range -2 to +2, where `llm_confidence` is the `confidence` field (0-1) the tool call reports.
- `decay`: applied on read (during `select_next_topic`, not per-message) — linear, `0.3 * max(0, days_since_last_review - 14)`, capped at 15 points.

These constants are a starting point for Phase 3 tuning, not a final calibration — flagging so it isn't mistaken for validated pedagogy.

## 5. Tool Schemas (Pydantic-style contracts)

All student/topic-scoped tools take an implicit `student_profile_id` bound to the authenticated session — never trust the LLM to pass it.

```
retrieve_textbook(topic: str, keywords: list[str], exam_code: str)
  -> { sources: [{ chapter, section, content, citation }] }

get_student_profile()
  -> { exam, current_topic, mastery: {topic: score}, weaknesses: [str] }

get_learning_history(limit: int = 10)
  -> { sessions: [{ date, topics_covered, summary }] }

generate_practice_problem(topic: str, difficulty: int(1-10), type: str)
  -> { problem_id, prompt, expected_answer_type: "numeric"|"symbolic"|"free_response",
       tolerance: float | null }
  -- grading path depends on expected_answer_type; numeric answers are checked
     deterministically server-side, free_response goes through an LLM-graded rubric

update_mastery(topic: str, assessment: str, confidence: float(0-1),
                recommended_change: int)
  -> { accepted: bool, new_mastery: int }
  -- recommended_change is advisory only; mastery_service computes the real delta

select_next_topic()
  -> { topic, reason }

save_session_summary(topics_covered: list[str], summary: str,
                      misconceptions: list[str], recommendations: str)
  -> { session_id }
```

## 6. API Contract (frontend ↔ backend)

```
POST   /api/auth/register
POST   /api/auth/login
GET    /api/students/me
GET    /api/students/me/mastery
GET    /api/students/me/sessions
POST   /api/chat/message        -- streamed response (SSE or chunked)
GET    /api/chat/sessions/:id
```

The frontend never calls tools directly — only `/api/chat/message` triggers the orchestrator, which runs the tool-calling loop server-side.

## 7. RAG Design

- Chunk metadata includes `exam_code` so retrieval is filtered per exam even once FM/FAM corpora are added — no cross-exam bleed.
- Embedding model: OpenAI `text-embedding-3-small` (cost-appropriate for MVP; revisit if retrieval quality is insufficient).
- Retrieval is selective, not automatic per message (Section 18 of spec) — the LLM's `retrieve_textbook` tool call is the trigger, not a fixed pre-retrieval step.
- Per Section 50: retrieval returns cited excerpts sized for explanation, not full sections/chapters.

## 8. Folder Structure

```
reerg3/
  backend/
    app/
      api/            (Flask blueprints)
      services/
      models/
      tools/
      prompts/
      database/
    tests/
    migrations/
  frontend/
    src/
      app/            (Next.js routes)
      components/
      lib/
  docs/
```

## 9. Config & Secrets

- `.env` (gitignored) for `OPENAI_API_KEY`, `DATABASE_URL`, `JWT_SECRET`.
- A fresh `git init` scoped to `reerg3/` is needed before any commit — the current repo root sits one level up at `Downloads` and is tracking unrelated personal files plus an untracked `.env`. This should be sorted before Phase 1 work is committed anywhere.

## 10. Open Items (not blocking Phase 0, need answers before relevant phase)

- Numeric-answer grading tolerance conventions for Exam P problem types.
- Where the Exam P textbook source material will be provided/ingested from (mechanics, not rights — rights already confirmed).
- Managed vs. in-house auth revisit once user volume is real.
