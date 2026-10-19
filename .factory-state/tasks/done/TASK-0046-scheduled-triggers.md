# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0046
- Status: done
- Phase: triggers
- Owner: Thái Quí Nguyễn
- Created: 2026-10-19
- Updated: 2026-10-19
- Requirement IDs: REQ-0033
- Design IDs: DEC-0036
- Architecture IDs:

## Objective

Cron schedules that start workflow runs, managed from the editor.

## Scope

### In Scope

- Backend: `models/workflow_schedule.py`, migration `0027_schedules`, `repositories/schedules.py`, `services/cron.py`, `services/schedule_service.py`, `services/run_worker.py`, `api/deps.py`, `api/routes/triggers.py`, `schemas/trigger.py`, `core/errors.py`
- Frontend: `components/schedules-dialog.tsx`, editor menu and header, run history badge, locales
- Tests: `backend/tests/test_schedules.py`, `frontend/e2e/schedules.spec.ts`
- Docs: both READMEs, `docs/api-errors.md`

### Out Of Scope

- Extended cron syntax, holiday calendars

## Inputs

- `.factory-state/artifacts/REQ-0033-scheduled-runs.md`

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0033-scheduled-runs.md`
- Decision: `.factory-state/decisions/DEC-0036-scheduled-runs.md`
- Review: `.factory-state/artifacts/REV-0044-task-0046.md`
- QA: `.factory-state/artifacts/QA-0044-task-0046.md`

## Constraints

- Stacked on `factory/task-0045-auth-hardening` (PR #49): migration `0027` follows `0026`. The PR targets that branch; retarget to `develop` after #49 merges. Do not merge until the owner asks.

## Dependencies

- TASK-0045 (PR #49).

## Acceptance Criteria

- Same as REQ-0033.

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

- 2026-10-19: Filed from item 6 of the remaining-work report (answers the REQ-0004 open question); the owner asked to do it. Own five-field parser (no dependency), scheduler in `RunWorker.maintain()` with a conditional-update claim, `source="schedule"` through the job queue (the worker no longer hard-codes `api`). Editor dialog with presets, a live preview, toggles, and typed-name delete. REV-0044 has no blocking findings. QA-0044 passed. Task set to done. Stacked PR. Not merged.

## Handoff Notes

- Retarget the PR to `develop` once PR #49 is merged.
