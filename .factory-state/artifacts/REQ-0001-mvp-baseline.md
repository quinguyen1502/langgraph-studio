# Requirement

## Metadata

- Project: langgraph-studio
- Requirement ID: REQ-0001
- Status: Implemented
- Owner: Thái Quí Nguyễn
- Created: 2026-10-16
- Updated: 2026-10-16
- Source: project-specs.md (MVP Scope)

## Summary

MVP baseline: visual LangGraph builder, runner, auth and repo import. Provide the internal MVP that the owner requested and that now exists in the repository.

## Problem Or Opportunity

Provide the internal MVP that the owner requested and that now exists in the repository.

## Scope

### In Scope

- Builder canvas, palette, config panel, state schema editor
- Workflow JSON CRUD in SQLite, validation, compiler to StateGraph
- LLM (OpenAI-compatible or deterministic mock) and Tool (HTTP / registered function) nodes
- WebSocket streaming of per-node events; run history
- Email/password auth with JWT; per-user ownership; list page
- Import LangGraph repo via subprocess + per-import venv; Code nodes; original-graph runs

### Out Of Scope

- Production hardening, multi-tenancy, real sandboxing (see REQ-0010)

## Stakeholders Or Users

- Internal developers and learners using LangGraph Studio
- Project owner (administrator)

## Current Context

- `backend/app/compiler.py`, `backend/app/main.py`, `backend/app/auth.py`, `backend/app/importer.py`, `backend/app/sandbox/runner.py`
- `frontend/src/pages/*.tsx`, `frontend/src/components/import-dialog.tsx`
- `backend/tests/` (19 tests)
- `docs/screenshots/`

## Desired Behavior

Provide the internal MVP that the owner requested and that now exists in the repository.

## Business Rules

- Demo credentials admin@example.com/admin123 and default JWT secret are for local use only

## Constraints

- Mock/offline mode must keep working without API keys.
- Must not break existing auth/ownership rules.

## Acceptance Criteria

- `cd backend && .venv/bin/python -m pytest -q` passes (observed: 19 passed on 2026-10-16)
- `cd frontend && npm run build` passes with no type errors (observed 2026-10-16)
- Seeded example workflow runs end to end in mock mode via WebSocket for both `order_status` and `general` branches
- Unauthenticated requests to workflow APIs return 401; WebSocket without token is rejected
- Importing `langchain-ai/new-langgraph-project` produces a runnable workflow; importing `langchain-ai/react-agent` shows conditional edges and reports missing API keys clearly

## Edge Cases

- Missing credentials or unavailable external services produce clear `error` events.

## Assumptions

- Stack direction in `project-specs.md` (Preferred) remains in place.

## Open Questions

- Should the demo user be removed or disabled outside local development?

## Related Artifacts

- `project-specs.md`
- `.factory-state/artifacts/ARCH-0001-current-architecture.md`
- `.factory-state/artifacts/DISC-0001-project-context.md`
