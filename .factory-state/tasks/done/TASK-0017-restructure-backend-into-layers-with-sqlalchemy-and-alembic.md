# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0017
- Status: review
- Owner: Grok Bot (agent)
- Created: 2026-10-16
- Updated: 2026-10-16
- Requirement IDs: REQ-0001
- Design IDs:
- Architecture IDs: ARCH-0001

## Objective

Restructure the backend into small, clear layers (core, models, schemas, repositories, services, api routers/deps, engine). Replace raw SQL with SQLAlchemy 2.0 ORM and Alembic migrations, without changing behaviour.

## Scope

### In Scope

- Layered package layout with fixed import directions, enforced by a test.
- SQLAlchemy 2.0 typed models for `users`, `workflows`, `runs`; repositories replace all raw `sqlite3` SQL.
- Alembic setup and an initial migration matching the current schema, which also adopts pre-Alembic SQLite files.
- `DATABASE_URL` (Postgres-ready); SQLite stays the default and `STUDIO_DB` keeps working.
- Service unit tests with fake repositories; migration tests.
- Docs: DEC-0009, ARCH-0001 layer diagram, `docs/backend-architecture.md`, AGENTS.md rule, README, roadmap.

### Out Of Scope

- Running on Postgres in CI, Redis (TASK-0009).
- Porting PR #2 credentials code (mapping documented; done when #2 is rebased).
- Any API, WebSocket protocol, env var or frontend change.

## Inputs

- `backend/app/**` on the TASK-0004 branch (PR #7)

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0001-mvp-baseline.md`
- Decision: DEC-0009; Architecture: ARCH-0001

## Expected Outputs

- `backend/app/{core,models,schemas,repositories,services,api,engine,migrations}`; `backend/alembic.ini`
- Tests `test_services.py`, `test_db_migrations.py`, `test_layers.py`; REV-0006, QA-0006

## Constraints

- File moves use `git mv` to keep history; the existing tests keep passing (only import paths change).

## Dependencies

- TASK-0004 branch (PR #7): this branch is stacked on it.

## Acceptance Criteria

- No raw SQL in `backend/app`; schema created and upgraded by Alembic.
- An existing SQLite DB from the MVP starts without data loss.
- All backend tests, the frontend build and Playwright E2E pass.
- The layer import rules test passes.

## Validation Plan

- `cd backend && .venv/bin/python -m pytest -q --cov=app`
- `cd frontend && npm run build && npx playwright test`

## Assumptions

- Postgres support is "ready" (portable types, URL switch), not exercised in CI.

## Open Questions

- None

## Activity Log

- 2026-10-16: Created on owner request (Phase 1). Branch `factory/task-0017-restructure-backend-layers` based on the TASK-0004 branch. Owner decision: SQLAlchemy 2.0 ORM + Alembic (DEC-0009).
- 2026-10-16: Implemented; 70 backend tests (coverage 95%), build and 10 E2E pass. Moved todo -> review. REV-0006, QA-0006.

## Handoff Notes

- Merge after #7, before #2. PR #2 must be rebased; mapping in `docs/backend-architecture.md`.
