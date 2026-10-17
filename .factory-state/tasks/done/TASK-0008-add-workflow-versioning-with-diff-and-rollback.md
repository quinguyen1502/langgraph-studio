# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0008
- Previous ID: TASK-0006 (renumbered 2026-10-16, DEC-0007)
- Status: done
- Owner: Grok Bot (agent)
- Created: 2026-10-16
- Updated: 2026-10-16
- Requirement IDs: REQ-0005
- Design IDs: DEC-0015
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

- Phase 2 integrates into `develop`; stacked on TASK-0007 (PR #14).

## Open Questions

- None

## Delivered

- `workflow_versions` + `runs.workflow_version` (migration `0006_workflow_versions`, backfills v1).
- A version on every changing save, with author and timestamp. List, get, diff and restore endpoints; restore creates a new latest version.
- Runs record the version that executed; history shows `vN` or "unsaved".
- UI: a "Versions" dialog (list, compare A→B, restore with confirm). New error code `VERSION_NOT_FOUND` (catalog, docs, en/vi).
- Tests: `tests/test_versions.py`, `e2e/versions.spec.ts`.
- Docs: DEC-0015, ARCH-0001, backend-architecture, README, roadmap, REV-0012, QA-0012.

## Activity Log

- 2026-10-16: Implemented on `factory/task-0008-add-workflow-versioning-with-diff-and-rollback` (stacked on TASK-0007); moved to review.

- 2026-10-16: Renumbered TASK-0006 -> TASK-0008 per owner re-plan (DEC-0007).
- 2026-10-16: Created task during Factory import/onboarding.

- 2026-10-17: Status set to done to match the done/ folder. Previous Status was `review`. Review REV-0012. QA QA-0012.

## Handoff Notes

- Use branch `factory/task-0008-add-workflow-versioning-with-diff-and-rollback` when implementation begins.
