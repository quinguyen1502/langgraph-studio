# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0008
- Previous ID: TASK-0006 (renumbered 2026-10-16, DEC-0007)
- Status: backlog
- Owner:
- Created: 2026-10-16
- Updated: 2026-10-16
- Requirement IDs: REQ-0005
- Design IDs:
- Architecture IDs: ARCH-0001

## Objective

Implement REQ-0005: Add workflow versioning with diff and rollback.

## Scope

### In Scope

- Deliver the in-scope items of `.factory-state/artifacts/REQ-0005-workflow-versioning.md`

### Out Of Scope

- Out-of-scope items listed in REQ-0005

## Inputs

- `.factory-state/artifacts/REQ-0005-workflow-versioning.md`
- `.factory-state/artifacts/ARCH-0001-current-architecture.md`

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0005-workflow-versioning.md`
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

- Each save creates a new version with author and timestamp
- Run history records the version that executed
- Rollback restores a previous version as a new latest version

## Validation Plan

- `cd backend && .venv/bin/python -m pytest -q`
- `cd frontend && npm run build`
- Manual run of the seeded example

## Assumptions

- Integration branch is `main` (see DISC-0001).

## Open Questions

- None

## Activity Log

- 2026-10-16: Renumbered TASK-0006 -> TASK-0008 per owner re-plan (DEC-0007).
- 2026-10-16: Created task during Factory import/onboarding.

## Handoff Notes

- Use branch `factory/task-0008-add-workflow-versioning-with-diff-and-rollback` when implementation begins.
