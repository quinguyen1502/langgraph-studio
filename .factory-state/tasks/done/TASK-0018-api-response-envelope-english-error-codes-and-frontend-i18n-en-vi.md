# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0018
- Status: review
- Owner: Grok Bot (agent)
- Created: 2026-10-16
- Updated: 2026-10-16
- Requirement IDs: REQ-0001
- Design IDs:
- Architecture IDs: ARCH-0001

## Objective

Give every REST endpoint one response envelope with stable English error codes. Add English/Vietnamese i18n to the frontend.

## Scope

### In Scope

- Envelope `{success, data, error}` on all REST endpoints; central handlers for AppError, 422, 404/405 and unhandled 500; the expired-token header is kept.
- One error-code catalog (`core/errors.py`); English messages across the backend, including engine/validator/import text.
- Structured `error` on WebSocket error events (legacy `errors` kept; 4401 unchanged).
- react-i18next with en/vi locale files; a shadcn language switcher on the login screen and the app headers; choice persisted in `localStorage.lang`; default from the browser.
- Error-code translation with fallback to the English message; the API client unwraps the envelope.
- Docs: `docs/api-errors.md`, DEC-0010, ARCH-0001, AGENTS.md coding rules (DRY/SOLID/KISS), README.

### Out Of Scope

- Translating individual validator issues and node exception text (they stay English in `details`).
- `meta`/pagination (reserved).

## Related Artifacts

- Requirement: REQ-0001; Decision: DEC-0010; Architecture: ARCH-0001

## Dependencies

- TASK-0005 branch (PR #9): this branch is stacked on it.

## Acceptance Criteria

- Every REST response, success or error, uses the envelope; codes are UPPER_SNAKE and the catalog matches the docs and both locales (enforced by a test).
- The UI switches between en/vi and remembers the choice; API errors are translated by code.
- Backend tests, build/lint and E2E pass (including a language-switch test and an error-translation test).

## Validation Plan

- `cd backend && .venv/bin/python -m pytest -q`
- `cd frontend && npm run build && npm run lint && npx playwright test`

## Assumptions

- Existing E2E specs run with `locale: vi-VN` (they assert Vietnamese UI); `i18n.spec.ts` uses `en-US`.

## Open Questions

- None

## Activity Log

- 2026-10-16: Created on owner request (Phase 1). Branch `factory/task-0018-api-envelope-error-codes-i18n` based on the TASK-0005 branch (PR #9). Implemented; pytest 88 passed, build/lint OK, E2E 13 passed (4 screenshot specs skipped). Moved to review. REV-0007, QA-0007.

## Handoff Notes

- Merge after #9. API clients outside the frontend must now read `data`.
