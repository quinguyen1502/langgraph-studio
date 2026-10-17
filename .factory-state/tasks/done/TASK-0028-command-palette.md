# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0028
- Status: done
- Phase: 5 — Editor UX
- Owner:
- Created: 2026-10-17
- Updated: 2026-10-17
- Requirement IDs: REQ-0018
- Design IDs:
- Architecture IDs: ARCH-0001

## Objective

Implement REQ-0018: Command palette.

## Scope

### In Scope

- shadcn Command dialog (Mod+K) listing registry actions (TASK-0023), add-node by type, jump to node, open workflow, open settings pages
- Fuzzy search, en/vi labels, shows each action's shortcut

### Out Of Scope

- Plugin-provided commands

## Inputs

- `.factory-state/artifacts/REQ-0018-command-palette.md`
- `.factory-state/artifacts/ARCH-0001-current-architecture.md`

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0018-command-palette.md`
- Architecture: `.factory-state/artifacts/ARCH-0001-current-architecture.md`

- Review: `.factory-state/artifacts/REV-0027-task-0028.md`
- QA: `.factory-state/artifacts/QA-0027-task-0028.md`

## Expected Outputs

- Implementation, tests (unit + Playwright e2e), README update, screenshots (light/dark × en/vi)

## Constraints

- Strict shadcn, en/vi, DRY/SOLID/KISS; mock mode and existing tests keep passing

## Dependencies

- TASK-0023

## Acceptance Criteria

- Mod+K opens the palette anywhere in the app; Enter runs the highlighted action
- Adding a node from the palette places it in view and selects it
- e2e covers open, search and run

## Validation Plan

- `cd backend && .venv/bin/python -m pytest -q`
- `cd frontend && npm run build && npx playwright test`

## Assumptions

- Draft PR into `develop`, stacked like the other tasks.

## Open Questions

- None yet

## Activity Log

- 2026-10-17: Created in backlog (Phase 5: Editor UX) via `factory task create`.
- 2026-10-17: Approved by the owner (no longer a suggestion).

- 2026-10-17: Status set to done to match the done/ folder. Previous Status was `backlog`. Review REV-0027. QA QA-0027.

## Handoff Notes

- Use branch `factory/task-0028-command-palette` when implementation begins.
