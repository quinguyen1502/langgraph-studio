# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0006
- Previous ID: TASK-0005 (renumbered 2026-10-16, DEC-0007)
- Status: backlog
- Owner:
- Created: 2026-10-16
- Updated: 2026-10-16
- Requirement IDs: REQ-0003
- Design IDs:
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

- Integration branch is `main` (see DISC-0001).

## Open Questions

- Who may approve: owner only or any authenticated user?

## Activity Log

- 2026-10-16: Renumbered TASK-0005 -> TASK-0006 per owner re-plan (DEC-0007).
- 2026-10-16: Created task during Factory import/onboarding.

## Handoff Notes

- Use branch `factory/task-0006-add-human-in-the-loop-interrupt-and-resume` when implementation begins.
