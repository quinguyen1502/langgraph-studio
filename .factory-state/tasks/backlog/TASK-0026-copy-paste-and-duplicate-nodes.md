# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0026
- Status: backlog
- Phase: 5 — Editor UX (suggestion)
- Owner:
- Created: 2026-10-17
- Updated: 2026-10-17
- Requirement IDs: REQ-0016
- Design IDs:
- Architecture IDs: ARCH-0001

## Objective

Implement REQ-0016: Copy, paste and duplicate nodes. Suggested follow-on; needs owner approval before it moves to todo.

## Scope

### In Scope

- Mod+C / Mod+X / Mod+V and Mod+D through the TASK-0023 registry; paste at the cursor with new ids
- Internal edges are kept, dangling ones dropped; Start/End are never duplicated
- Clipboard payload is versioned JSON so pasting into another workflow works; credential references are kept only if the user owns them

### Out Of Scope

- Pasting arbitrary external JSON as nodes

## Inputs

- `.factory-state/artifacts/REQ-0016-copy-paste-nodes.md`
- `.factory-state/artifacts/ARCH-0001-current-architecture.md`

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0016-copy-paste-nodes.md`
- Architecture: `.factory-state/artifacts/ARCH-0001-current-architecture.md`

## Expected Outputs

- Implementation, tests (unit + Playwright e2e), README update, screenshots (light/dark × en/vi)

## Constraints

- Strict shadcn, en/vi, DRY/SOLID/KISS; mock mode and existing tests keep passing

## Dependencies

- TASK-0023
- TASK-0024

## Acceptance Criteria

- Copy → paste duplicates nodes and their internal edges with fresh ids
- Paste into another workflow works
- Each paste is one undo step (TASK-0024)

## Validation Plan

- `cd backend && .venv/bin/python -m pytest -q`
- `cd frontend && npm run build && npx playwright test`

## Assumptions

- Draft PR into `develop`, stacked like the other tasks.

## Open Questions

- Suggestion, not yet approved by the owner.

## Activity Log

- 2026-10-17: Created in backlog (Phase 5: Editor UX) via `factory task create`; marked as a suggestion.

## Handoff Notes

- Use branch `factory/task-0026-copy-paste-nodes` when implementation begins.
