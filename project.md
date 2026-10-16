# Project

## Name

langgraph-studio

## Domain

- Developer tooling for LLM agent workflows (LangGraph)

## Actors

- Internal developer / learner (authenticated user)
- Project owner / administrator
- External LangGraph repositories (import source)

## Modules

- `frontend/` — React SPA: login/register, workflow list, editor (canvas, palette, config, run panel), import dialog
- `backend/app/` — layered FastAPI backend (DEC-0009, `docs/backend-architecture.md`):
  - `main.py` app factory; `api/` routers (REST + `/ws/run`), deps, error handlers
  - `services/` business rules; `repositories/` SQLAlchemy queries; `models/` ORM models + `Database`; `migrations/` Alembic
  - `engine/` validator, StateGraph compiler, nodes, LLM/tools, runtime streaming, limits, repo import + `sandbox/runner.py`
  - `core/` config (env vars), security (hashing, JWT), domain errors; `schemas/` Pydantic DTOs
- `backend/tests/` — pytest suite

## Constraints

- Internal use; SQLite for MVP; must run offline in mock mode
- Imported code only runs in a subprocess with its own venv
- UI: shadcn/ui components and theme tokens only, no hard-coded colours (DEC-0008, `docs/ui-conventions.md`)

## Declared Technology Direction

- Frontend: React + TypeScript (Vite), @xyflow/react, Tailwind CSS v4, shadcn/ui (Preferred, DEC-0001; observed in `frontend/package.json`)
- Mobile: none
- Backend: FastAPI + langgraph, Python 3.13 (Preferred; observed in `backend/requirements.txt`)
- Database: SQLite (Preferred; observed); PostgreSQL + Redis proposed (REQ-0008)
- Infrastructure: `dev.sh` local script (observed); Docker Compose proposed
- Ci Cd: GitHub Actions (Approved, DEC-0001; `.github/workflows/ci.yml` + `factory-verify.yml`)
- Deployment: Unknown
- Testing: pytest, tsc/vite build, Playwright screenshots (Preferred; observed)

## Technology Discovery

- Install: `./dev.sh` first run (creates `backend/.venv`, `pip install -e "backend[dev]"`, `npm install`); Factory: `factory deps apply --allow-network`
- Run: `./dev.sh` (observed: backend :8000, frontend :5173)
- Test: `cd backend && .venv/bin/python -m pytest -q` (observed: 19 passed, 2026-10-16)
- Build: `cd frontend && npm run build` (observed: passes)
- Lint: `cd frontend && npm run lint` (oxlint; observed passing via `factory verify run`)
- Typecheck: `cd frontend && npx tsc -b` (observed, part of build)
- Format: Unknown
- Migration: none (schema created/migrated at startup)

## Assumptions

- Stack choices are Preferred by owner decision (DEC-0001); CI is Approved.

## Open Questions

- None (resolved by DEC-0001..DEC-0005).
