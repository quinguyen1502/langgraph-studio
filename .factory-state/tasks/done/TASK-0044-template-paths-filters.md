# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0044
- Status: done
- Phase: editor maintenance
- Owner: Thái Quí Nguyễn
- Created: 2026-10-18
- Updated: 2026-10-18
- Requirement IDs: REQ-0031
- Design IDs: DEC-0034
- Architecture IDs:

## Objective

Template paths and filters in the engine, validator, and template editor.

## Scope

### In Scope

- `backend/app/engine/templating.py`, `engine/validator.py`, `core/errors.py` (`TEMPLATE_REF_INVALID`)
- `frontend/src/lib/state-refs.ts`, `components/template-editor.tsx`, locale files
- Tests: `backend/tests/test_template_refs.py`, `backend/tests/fixtures/template_refs.json`, `frontend/src/lib/__tests__/state-refs.test.ts`, `frontend/e2e/template-filters.spec.ts`
- `README.md`, `README.vi.md`, `docs/api-errors.md`, `docs/ui-conventions.md`

### Out Of Scope

- Expressions, loops, custom filters

## Inputs

- `.factory-state/artifacts/REQ-0031-template-paths-filters.md`

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0031-template-paths-filters.md`
- Decision: `.factory-state/decisions/DEC-0034-template-paths-filters.md`
- Review: `.factory-state/artifacts/REV-0042-task-0044.md`
- QA: `.factory-state/artifacts/QA-0042-task-0044.md`

## Constraints

- Branch from `develop` (`4ee1ccd`). One PR into `develop`. Do not merge until the owner asks.

## Dependencies

- TASK-0041 (PR #44), merged. Independent of TASK-0043 (PR #47); both touch `template-editor.tsx` in different places.

## Acceptance Criteria

- Same as REQ-0031.

## Validation Plan

- `cd backend && .venv/bin/python -m pytest -q`
- `cd frontend && npx tsc -b && npx vitest run && npx oxlint && npx vite build`
- `cd frontend && PW_CHROME=... E2E_UVICORN=../backend/.venv/bin/uvicorn npx playwright test`
- `git diff --check`

## Assumptions

- `factory ready` does not exit 0 here (the CLI needs `textual`). GitHub Actions does not run (billing). Local checks are the evidence.

## Open Questions

- None

## Activity Log

- 2026-10-18: Filed from item 8 of the remaining-work report; the owner asked to do it. One parser per side, sharing `template_refs.json`. The first error code name, `TEMPLATE_INVALID`, already existed for template files and overrode its message (a `KeyError` in `test_templates.py`); renamed to `TEMPLATE_REF_INVALID`. The validator now checks the Human prompt and the HTTP URL and body too. The editor shows the filter chain on tags, suggests filters after `|`, and opens a tag as text on double-click. REV-0042 has no blocking findings. QA-0042 passed. Task set to done. PR into `develop`. Not merged.

## Handoff Notes

- None.
