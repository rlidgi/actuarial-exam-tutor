# Actuarial Tutor AI Platform

MVP scope: SOA Exam P, with the schema and services already exam-scoped so FM and FAM
can be added later without rework. See [docs/PHASE0_ARCHITECTURE.md](docs/PHASE0_ARCHITECTURE.md)
for the full technical plan.

## Structure

- `backend/` — Flask API (auth, student/mastery data, tutor orchestration in Phase 2)
- `frontend/` — Next.js app
- `docs/` — architecture and planning docs

## Backend setup

```
python -m venv venv
venv\Scripts\activate
pip install -r backend/requirements.txt
copy backend\.env.example backend\.env   # then fill in real secrets
```

Requires a running PostgreSQL instance matching `DATABASE_URL` in `backend/.env`.

```
cd backend
set FLASK_APP=wsgi.py
flask db upgrade
flask run --with-threads
```

`--with-threads` matters: the study manual/formula sheet responses are large
(hundreds of KB), and Next.js dev mode fires each page's data-fetch effect
twice on mount (React Strict Mode). Werkzeug's dev server can't reliably
serve two large concurrent requests without it -- one stalls and the
connection resets, which surfaces in the browser as a generic "Failed to
fetch". Production is unaffected (see `backend/Dockerfile` -- gunicorn with
4 workers already handles concurrency correctly).

Run tests (uses in-memory SQLite, no Postgres needed):

```
cd backend
pytest
```

## Frontend setup

```
cd frontend
npm install
copy .env.local.example .env.local
npm run dev
```

## Status

Phase 1 (foundation) complete: project structure, backend API skeleton, DB models and
migrations, JWT auth, student/mastery read endpoints, test framework, frontend skeleton.

Phase 2 (AI tutor integration — OpenAI tool-calling loop, RAG) not yet started.
