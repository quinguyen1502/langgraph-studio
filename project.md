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
- `backend/app/main.py` — FastAPI REST + WebSocket, SQLite persistence
- `backend/app/compiler.py` — validation, StateGraph compiler, LLM/tool execution, streaming
- `backend/app/auth.py` — password hashing, JWT
- `backend/app/importer.py`, `backend/app/sandbox/runner.py` — repo import and subprocess execution
- `backend/tests/` — pytest suite

## Constraints

- Internal use; SQLite for MVP; must run offline in mock mode
- Imported code only runs in a subprocess with its own venv

## Declared Technology Direction

- Frontend: React + TypeScript (Vite), @xyflow/react, Tailwind CSS v4, shadcn/ui (Preferred; observed in `frontend/package.json`)
- Mobile: none
- Backend: FastAPI + langgraph, Python 3.13 (Preferred; observed in `backend/requirements.txt`)
- Database: SQLite (Preferred; observed); PostgreSQL + Redis proposed (REQ-0008)
- Infrastructure: `dev.sh` local script (observed); Docker Compose proposed
- Ci Cd: GitHub Actions (Proposed; not present yet — TASK-0002)
- Deployment: Unknown
- Testing: pytest, tsc/vite build, Playwright screenshots (Preferred; observed)

## Technology Discovery

- Install: `./dev.sh` first run (observed: creates `backend/.venv`, installs `backend/requirements.txt`, runs `npm install`)
- Run: `./dev.sh` (observed: backend :8000, frontend :5173)
- Test: `cd backend && .venv/bin/python -m pytest -q` (observed: 19 passed, 2026-10-16)
- Build: `cd frontend && npm run build` (observed: passes)
- Lint: Unknown (frontend has `.oxlintrc.json` but no lint script verified)
- Typecheck: `cd frontend && npx tsc -b` (observed, part of build)
- Format: Unknown
- Migration: none (schema created/migrated at startup)

## Assumptions

- Stack choices are recorded as Preferred pending explicit owner approval in Factory terms.

## Open Questions

- Should the stack be marked `Approved`? (Factory `ready` would then require a scaffold marker; see DISC-0001.)
- Integration branch: `main` (detected) vs. introducing `develop`.
