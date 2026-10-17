# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0015
- Previous ID: TASK-0004 (renumbered 2026-10-16, DEC-0007)
- Status: doing
- Owner:
- Created: 2026-10-16
- Updated: 2026-10-17
- Requirement IDs: REQ-0009
- Design IDs:
- Architecture IDs: ARCH-0001

## Objective

Phase 4 (last). Harden the experimental repo-import feature and run it in a container sandbox. Implement REQ-0009: Run repo imports inside a container sandbox.

## Scope

### In Scope

- Put repo import behind feature flag `STUDIO_ENABLE_IMPORT` (default **off**): API returns 404/403 and UI hides the Import button when disabled; README marks import as experimental
- Import hardening: job persistence, cleanup of old import workspaces, size/time limits
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

- With `STUDIO_ENABLE_IMPORT` unset, `/api/import*` is unavailable and the Import button is hidden; with it set to `1`, current behaviour works
- Import and run of `new-langgraph-project` succeed inside the container with identical events
- Imported code cannot read files outside its import directory or the server environment
- A run exceeding limits is killed and reported as an error event

## Validation Plan

- `cd backend && .venv/bin/python -m pytest -q`
- `cd frontend && npm run build`
- Manual run of the seeded example

## Assumptions

- Task branch is cut from `develop`. `factory.yaml` and DEC-0002 still name `main`, and `main` does not contain the merged product. PRs for this task target `develop`, matching Phase 2–5.
- Sandbox runtime for this task is Docker (OCI `runc`), including Docker Desktop on macOS. gVisor and Firecracker are out of scope. The owner did not pick a runtime, so this is the working assumption and can be overridden before implementation.

## Open Questions

- None for the runtime choice. Override the Docker assumption above if the host must be gVisor or Firecracker.

## Activity Log

- 2026-10-16: Renumbered TASK-0004 -> TASK-0015 per owner re-plan (DEC-0007).
- 2026-10-16: Created task during Factory import/onboarding.
- 2026-10-17: Owner said to start. Moved backlog -> todo -> doing on `factory/task-0015-run-repo-imports-inside-a-container-sandbox`. Runtime assumption: Docker.

## Handoff Notes

- Use branch `factory/task-0015-run-repo-imports-inside-a-container-sandbox` when implementation begins.
