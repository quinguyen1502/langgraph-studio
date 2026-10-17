# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0023
- Status: done
- Phase: 5 — Editor UX
- Owner:
- Created: 2026-10-17
- Updated: 2026-10-17
- Requirement IDs: REQ-0013
- Design IDs:
- Architecture IDs: ARCH-0001

## Objective

Implement REQ-0013: Editor hotkeys and shortcut cheatsheet.

## Scope

### In Scope

- A single shortcut registry (id, keys per platform: Ctrl on Windows/Linux, ⌘ on macOS, label key, handler) used by the editor and the cheatsheet
- Shortcuts: save (Mod+S), run (Mod+Enter), stop run, delete selection (Delete/Backspace), select all (Mod+A), fit view (Shift+1), zoom in/out, close panel (Esc), open cheatsheet (? or Mod+/)
- Shortcuts are ignored while typing in an input, textarea, select or code editor
- Cheatsheet: shadcn Dialog grouped by category (General, Canvas, Run), en/vi labels, shown keys match the platform

### Out Of Scope

- User-defined remapping
- Shortcuts outside the editor

## Inputs

- `.factory-state/artifacts/REQ-0013-editor-hotkeys.md`
- `.factory-state/artifacts/ARCH-0001-current-architecture.md`

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0013-editor-hotkeys.md`
- Architecture: `.factory-state/artifacts/ARCH-0001-current-architecture.md`

- Review: `.factory-state/artifacts/REV-0022-task-0023.md`
- QA: `.factory-state/artifacts/QA-0022-task-0023.md`

## Expected Outputs

- Implementation, tests (unit + Playwright e2e), README update, screenshots (light/dark × en/vi)

## Constraints

- Strict shadcn, en/vi, DRY/SOLID/KISS; mock mode and existing tests keep passing

## Dependencies

- None

## Acceptance Criteria

- Mod+S saves without the browser's save-page dialog; Mod+Enter starts a run
- Delete removes the selected nodes/edges (except Start/End) and is ignored inside text fields
- ? opens the cheatsheet; every registered shortcut appears there with en/vi labels
- e2e covers save, delete and the cheatsheet

## Validation Plan

- `cd backend && .venv/bin/python -m pytest -q`
- `cd frontend && npm run build && npx playwright test`

## Assumptions

- Draft PR into `develop`, stacked like the other tasks.

## Open Questions

- Interacts with TASK-0024 (undo/redo keys).

## Activity Log

- 2026-10-17: Created in backlog (Phase 5: Editor UX) via `factory task create`.

- 2026-10-17: Status set to done to match the done/ folder. Previous Status was `backlog`. Review REV-0022. QA QA-0022.

## Handoff Notes

- Use branch `factory/task-0023-editor-hotkeys` when implementation begins.
