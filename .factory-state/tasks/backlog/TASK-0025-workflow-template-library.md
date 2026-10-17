# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0025
- Status: backlog
- Phase: 5 — Editor UX
- Owner:
- Created: 2026-10-17
- Updated: 2026-10-17
- Requirement IDs: REQ-0015
- Design IDs:
- Architecture IDs: ARCH-0001

## Objective

Implement REQ-0015: Workflow template library.

## Scope

### In Scope

- Built-in starter templates (e.g. chatbot, RAG Q&A, approval flow, router with conditions) seeded read-only
- New workflow → pick a template (gallery with name, description, node preview) or blank
- Save as template from the editor (name, description; personal, or org-wide for admins)
- Import/export a template as JSON (validated against the workflow schema; credentials and secrets never exported)
- API with the response envelope and English error codes (catalog, docs/api-errors.md, en+vi); Alembic migration that works on SQLite and Postgres

### Out Of Scope

- Public template marketplace
- Versioning of templates

## Inputs

- `.factory-state/artifacts/REQ-0015-template-library.md`
- `.factory-state/artifacts/ARCH-0001-current-architecture.md`

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0015-template-library.md`
- Architecture: `.factory-state/artifacts/ARCH-0001-current-architecture.md`

## Expected Outputs

- Implementation, tests (unit + Playwright e2e), README update, screenshots (light/dark × en/vi)

## Constraints

- Strict shadcn, en/vi, DRY/SOLID/KISS; mock mode and existing tests keep passing

## Dependencies

- None

## Acceptance Criteria

- Creating from a template produces an independent workflow that runs in mock mode
- Export → import round-trips a template; invalid files get a translated error code
- Exported files contain no credential ids or secrets
- Backend tests (SQLite + Postgres), e2e for gallery, save-as-template and import

## Validation Plan

- `cd backend && .venv/bin/python -m pytest -q`
- `cd frontend && npm run build && npx playwright test`

## Assumptions

- Draft PR into `develop`, stacked like the other tasks.

## Open Questions

- Org-wide templates reuse users.is_admin (TASK-0022) until RBAC (TASK-0014).

## Activity Log

- 2026-10-17: Created in backlog (Phase 5: Editor UX) via `factory task create`.

## Handoff Notes

- Use branch `factory/task-0025-template-library` when implementation begins.
