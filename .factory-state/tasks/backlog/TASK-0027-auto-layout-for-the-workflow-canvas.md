# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0027
- Status: backlog
- Phase: 5 — Editor UX (suggestion)
- Owner:
- Created: 2026-10-17
- Updated: 2026-10-17
- Requirement IDs: REQ-0017
- Design IDs:
- Architecture IDs: ARCH-0001

## Objective

Implement REQ-0017: Auto-layout for the workflow canvas. Suggested follow-on; needs owner approval before it moves to todo.

## Scope

### In Scope

- Layout action (toolbar + shortcut) using a layered graph layout (e.g. dagre/elkjs), direction LR/TB
- Respects node sizes, keeps Start first / End last, handles loops and parallel branches
- Result is one undo step and is saved like any move

### Out Of Scope

- Live/continuous layout while editing

## Inputs

- `.factory-state/artifacts/REQ-0017-auto-layout.md`
- `.factory-state/artifacts/ARCH-0001-current-architecture.md`

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0017-auto-layout.md`
- Architecture: `.factory-state/artifacts/ARCH-0001-current-architecture.md`

## Expected Outputs

- Implementation, tests (unit + Playwright e2e), README update, screenshots (light/dark × en/vi)

## Constraints

- Strict shadcn, en/vi, DRY/SOLID/KISS; mock mode and existing tests keep passing

## Dependencies

- TASK-0024

## Acceptance Criteria

- Layout produces no overlapping nodes on the seeded examples
- Undo restores the previous positions
- Works for imported workflows

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

- Use branch `factory/task-0027-auto-layout` when implementation begins.
