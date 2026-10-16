# Decision Record

## Metadata

- Project: langgraph-studio
- Decision ID: DEC-0009
- Status: Accepted
- Owner: Thái Quí Nguyễn
- Created: 2026-10-16
- Updated: 2026-10-16
- Related Requirements: REQ-0001, REQ-0008
- Related Architecture: ARCH-0001
- Related Tasks: TASK-0017 (first application), TASK-0005 (port), TASK-0009 (Postgres)

## Context

`backend/app/main.py` mixed routing, SQL, business rules and the run loop; `compiler.py` mixed validation, templating, tools, LLM calls and streaming. Data access was raw `sqlite3` with an inline startup migration.

## Decision

1. The backend is split into layers: `core`, `models`, `schemas`, `repositories`, `services`, `api` (routers + deps + error handlers) and `engine`. Import directions are fixed (`docs/backend-architecture.md`) and enforced by `tests/test_layers.py`.
2. Data access uses **SQLAlchemy 2.0 ORM** (typed `Mapped` models) instead of raw SQL. Schema changes go through **Alembic** migrations; revision `0001_initial` matches the MVP schema and adopts pre-Alembic SQLite files without data loss.
3. SQLite stays the default. `DATABASE_URL` selects another database (Postgres-ready); `STUDIO_DB` keeps working.
4. Services raise domain errors (`core.errors`) and never import FastAPI.

## Consequences

- New dependencies: `sqlalchemy>=2.0`, `alembic>=1.13`.
- API paths, WebSocket protocol, env vars and stored data are unchanged.
- Open PRs touching `main.py`/`compiler.py` (PR #2) need a rebase; the mapping is in `docs/backend-architecture.md`.

## Approval

- Approved By: Thái Quí Nguyễn (owner), 2026-10-16
