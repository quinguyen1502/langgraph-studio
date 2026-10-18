# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0015
- Previous ID: TASK-0004 (renumbered 2026-10-16, DEC-0007)
- Status: review
- Owner:
- Created: 2026-10-16
- Updated: 2026-10-18
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
- 2026-10-17: Implementation landed on this branch. Runtime is Docker when `STUDIO_ENABLE_IMPORT=1`. `STUDIO_IMPORT_RUNTIME=subprocess` remains for tests and machines without Docker. gVisor and Firecracker stay out of scope. Task stays in doing.
- 2026-10-18: Validation. `backend/.venv` is Python 3.14 without pytest, so the suite ran with `/tmp/lgs-qa-venv` (Python 3.12): 276 passed, 10 skipped. `cd frontend && npm run build` passed. UI: with the flag unset, `#import-btn` is absent (desktop and 390px) and `POST /api/import` is 404 `IMPORT_DISABLED`; with `STUDIO_ENABLE_IMPORT=1` the button opens the URL and zip tabs. Task stays in doing.
- 2026-10-18: Live Docker check on Docker Desktop (`python:3.12-slim`, CLI not on PATH; used `/Applications/Docker.app/Contents/Resources/bin/docker`). `new-langgraph-project` imported and ran in the container: nodes `__start__`, `call_model`, `__end__`, state `output from call_model. Configured with studio`. A probe could write inside the job dir and could not read a host sentinel or `JWT_SECRET` / `STUDIO_DB`. A 30s sleep was killed and reported `Sandbox stopped (time limit (12s)).`. Fix: `run_imported` uses `lexists` because the venv python is a symlink to the image interpreter. The API also uses Docker Desktop's bundled CLI when `docker` is not on `PATH`. Task stays in doing.
- 2026-10-18: Moved doing -> review. Backend suite after the symlink and Docker CLI fixes: 278 passed, 10 skipped (`/tmp/lgs-qa-venv`, Python 3.12). `cd frontend && npm run build` passed before those backend-only fixes and the frontend did not change after it. Live Docker import passed. Review and QA artifacts are not written yet. Task is not done.
- 2026-10-18: Agent review REV-0029 (`approved for QA`, no blocking findings) and QA-0029 (`pass with follow-up`). Pytest and `npm run build` were re-run on `4d3813b`: 278 passed, 10 skipped, 97.65s; frontend build exit 0. Task stays in `review`. Not done. Owner review on PR #33 is still pending.

## Handoff Notes

- Branch `factory/task-0015-run-repo-imports-inside-a-container-sandbox` is in review. Draft PR #33 targets `develop`.
- Review: `.factory-state/artifacts/REV-0029-task-0015-container-sandbox.md`. QA: `.factory-state/artifacts/QA-0029-task-0015-container-sandbox.md`.
- Do not merge and do not mark this task done until the owner asks. REQ-0009 stays Proposed.
- `frontend/package-lock.json` dev-metadata stays in `stash@{0}` (created on `develop`). Do not pop that stash onto this branch.
