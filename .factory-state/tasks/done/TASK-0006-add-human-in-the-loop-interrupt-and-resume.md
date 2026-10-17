# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0006
- Previous ID: TASK-0005 (renumbered 2026-10-16, DEC-0007)
- Status: done
- Owner: Grok Bot (agent)
- Created: 2026-10-16
- Updated: 2026-10-16
- Requirement IDs: REQ-0003
- Design IDs: DEC-0013
- Architecture IDs: ARCH-0001

## Objective

Implement REQ-0003: Add human-in-the-loop interrupt and resume.

## Scope

### In Scope

- Deliver the in-scope items of `.factory-state/artifacts/REQ-0003-human-in-the-loop.md`

### Out Of Scope

- Out-of-scope items listed in REQ-0003

## Inputs

- `.factory-state/artifacts/REQ-0003-human-in-the-loop.md`
- `.factory-state/artifacts/ARCH-0001-current-architecture.md`

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0003-human-in-the-loop.md`
- Architecture: `.factory-state/artifacts/ARCH-0001-current-architecture.md`
- Discovery: `.factory-state/artifacts/DISC-0001-project-context.md`

## Expected Outputs

- Implementation, tests, README update
- Design/architecture artifact if the requirement changes boundaries

## Constraints

- Mock mode and existing tests must keep passing

## Dependencies

- TASK-0002 (CI) recommended first

## Acceptance Criteria

- A run reaching an interrupt node stops with status `waiting` and is listed as pending
- Submitting a response resumes the same run from the checkpoint and completes
- Resume works after a server restart (persistent checkpointer)

## Validation Plan

- `cd backend && .venv/bin/python -m pytest -q`
- `cd frontend && npm run build`
- Manual run of the seeded example

## Assumptions

- Phase 2 integrates into `develop`; stacked on TASK-0010 (PR #12).

## Open Questions

- Who may approve: owner only or any authenticated user? **Resolved (DEC-0013): owner only, until RBAC (TASK-0014).**

## Delivered

- Node type `human` (validator, engine `Interrupt`, resume entry point); WS events `run_waiting` / `run_resumed`; resume over `/ws/run`; `GET /api/runs/pending`; cancel of waiting runs.
- Migration `0004_hitl` (`runs.owner` backfilled, `runs.checkpoint`); error codes `RUN_NOT_WAITING`, `RUN_RESPONSE_INVALID` (catalog, docs, en/vi).
- UI: Human node (palette, inspector, `node-human` theme token), Human panel (approve / reject / text), waiting status in trace and history, "Waiting for you" card on the workflow list, `?run=` deep link.
- Tests: `tests/test_hitl.py`, `e2e/hitl.spec.ts`. Docs: DEC-0013, ARCH-0001, backend-architecture, README, roadmap, REV-0010, QA-0010.

## Activity Log

- 2026-10-16: Implemented on `factory/task-0006-add-human-in-the-loop-interrupt-and-resume` (stacked on TASK-0010); moved to review.

- 2026-10-16: Renumbered TASK-0005 -> TASK-0006 per owner re-plan (DEC-0007).
- 2026-10-16: Created task during Factory import/onboarding.

- 2026-10-17: Status set to done to match the done/ folder. Previous Status was `review`. Review REV-0010. QA QA-0010.

## Handoff Notes

- Use branch `factory/task-0006-add-human-in-the-loop-interrupt-and-resume` when implementation begins.
