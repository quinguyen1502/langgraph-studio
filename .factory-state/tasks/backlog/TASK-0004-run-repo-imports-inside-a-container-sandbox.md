# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0004
- Status: backlog
- Owner:
- Created: 2026-10-16
- Updated: 2026-10-16
- Requirement IDs: REQ-0009
- Design IDs:
- Architecture IDs: ARCH-0001

## Objective

Implement REQ-0009: Run repo imports inside a container sandbox.

## Scope

### In Scope

- Deliver the in-scope items of `.factory-state/artifacts/REQ-0009-sandboxed-imports.md`

### Out Of Scope

- Out-of-scope items listed in REQ-0009

## Inputs

- `.factory-state/artifacts/REQ-0009-sandboxed-imports.md`
- `.factory-state/artifacts/ARCH-0001-current-architecture.md`

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0009-sandboxed-imports.md`
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

- Import and run of `new-langgraph-project` succeed inside the container with identical events
- Imported code cannot read files outside its import directory or the server environment
- A run exceeding limits is killed and reported as an error event

## Validation Plan

- `cd backend && .venv/bin/python -m pytest -q`
- `cd frontend && npm run build`
- Manual run of the seeded example

## Assumptions

- Integration branch is `main` (see DISC-0001).

## Open Questions

- Container runtime available on the target host (Docker, gVisor, Firecracker)?

## Activity Log

- 2026-10-16: Created task during Factory import/onboarding.

## Handoff Notes

- Use branch `factory/task-0004-run-repo-imports-inside-a-container-sandbox` when implementation begins.
