# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0014
- Previous ID: TASK-0013 (renumbered 2026-10-16, DEC-0007)
- Status: backlog
- Owner:
- Created: 2026-10-16
- Updated: 2026-10-16
- Requirement IDs: REQ-0012
- Design IDs:
- Architecture IDs: ARCH-0001

## Objective

Implement REQ-0012: Add RBAC and workflow sharing.

## Scope

### In Scope

- Deliver the in-scope items of `.factory-state/artifacts/REQ-0012-rbac-sharing.md`

### Out Of Scope

- Out-of-scope items listed in REQ-0012

## Inputs

- `.factory-state/artifacts/REQ-0012-rbac-sharing.md`
- `.factory-state/artifacts/ARCH-0001-current-architecture.md`

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0012-rbac-sharing.md`
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

- A viewer can open and run but not edit a shared workflow
- An editor can edit; only owner/admin can delete or share
- All existing ownership tests still pass

## Validation Plan

- `cd backend && .venv/bin/python -m pytest -q`
- `cd frontend && npm run build`
- Manual run of the seeded example

## Assumptions

- Integration branch is `main` (see DISC-0001).

## Open Questions

- Is SSO (Google/Microsoft) required with RBAC?

## Activity Log

- 2026-10-16: Renumbered TASK-0013 -> TASK-0014 per owner re-plan (DEC-0007).
- 2026-10-16: Created task during Factory import/onboarding.

## Handoff Notes

- Use branch `factory/task-0014-add-rbac-and-workflow-sharing` when implementation begins.
