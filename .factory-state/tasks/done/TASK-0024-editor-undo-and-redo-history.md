# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0024
- Status: done
- Phase: 5 — Editor UX
- Owner:
- Created: 2026-10-17
- Updated: 2026-10-17
- Requirement IDs: REQ-0014
- Design IDs:
- Architecture IDs: ARCH-0001

## Objective

Implement REQ-0014: Editor undo and redo history.

## Scope

### In Scope

- History of editor snapshots (nodes, edges, state schema, node config), coalescing drags and typing bursts, capped size (e.g. 100)
- Undo (Mod+Z) / redo (Mod+Shift+Z, Mod+Y) via the TASK-0023 registry, plus toolbar buttons with disabled states
- History resets on load / version restore; unsaved-changes tracking stays correct after undo back to the saved state

### Out Of Scope

- Server-side history (versions already cover saved states)
- Collaborative editing

## Inputs

- `.factory-state/artifacts/REQ-0014-editor-undo-redo.md`
- `.factory-state/artifacts/ARCH-0001-current-architecture.md`

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0014-editor-undo-redo.md`
- Architecture: `.factory-state/artifacts/ARCH-0001-current-architecture.md`

- Review: `.factory-state/artifacts/REV-0023-task-0024.md`
- QA: `.factory-state/artifacts/QA-0023-task-0024.md`

## Expected Outputs

- Implementation, tests (unit + Playwright e2e), README update, screenshots (light/dark × en/vi)

## Constraints

- Strict shadcn, en/vi, DRY/SOLID/KISS; mock mode and existing tests keep passing

## Dependencies

- TASK-0023

## Acceptance Criteria

- Add, delete, move, connect and config edits are each undoable and redoable
- A drag is one step, not one per pixel; typing in a field is coalesced
- Undo back to the saved snapshot clears the unsaved marker
- Unit tests for the history reducer; e2e for delete → undo → redo

## Validation Plan

- `cd backend && .venv/bin/python -m pytest -q`
- `cd frontend && npm run build && npx playwright test`

## Assumptions

- Draft PR into `develop`, stacked like the other tasks.

## Open Questions

- None yet

## Activity Log

- 2026-10-17: Created in backlog (Phase 5: Editor UX) via `factory task create`.

- 2026-10-17: Status set to done to match the done/ folder. Previous Status was `backlog`. Review REV-0023. QA QA-0023.

## Handoff Notes

- Use branch `factory/task-0024-editor-undo-redo` when implementation begins.
