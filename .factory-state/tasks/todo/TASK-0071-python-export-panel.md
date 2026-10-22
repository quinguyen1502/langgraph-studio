# Task

## Metadata

- Project: superstep
- Task ID: TASK-0071
- Status: todo
- Owner: Thái Quí Nguyễn
- Created: 2026-10-22
- Updated: 2026-10-22
- Requirement IDs: REQ-0043
- Design IDs: none (UX set in REQ-0043)
- Architecture IDs: DEC-0008, DEC-0045

## Objective

Show the exported Python next to the canvas, follow the selected node, and let the user copy or download the file.

## Scope

### In Scope

- **View as Python** in the editor header and in the command palette, for workflows (not imported repositories).
- A read-only panel beside the canvas (same place and behaviour as the run and tests panels), with CodeMirror Python
  (as the Code node editor), for the version open in the editor (an unsaved graph: the panel says it shows the last
  saved version).
- Selecting a node on the canvas scrolls to and highlights its function; Start / End highlight their `START` / `END`
  edges, a Note its comment.
- **Copy** (toast) and **Download .py** (`<name>.py`).
- Loading and error states through `api()` and `errorText`; en and vi strings.
- E2E: open a template workflow, open the panel, click a node, the function is highlighted; download gives a `.py`
  file that contains `StateGraph`; the option is missing on an imported repository.

### Out Of Scope

- Editing the code; diffing two versions' code (the version diff exists for the graph).

## Inputs

- TASK-0070 (route, node markers).
- `frontend/src/components/editor/editor-header.tsx`, `editor-run-panel.tsx` / `editor-tests-panel.tsx` (panel
  pattern), `components/command-palette.tsx`, the Code node CodeMirror setup, `lib/api.ts`, locales.

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0043-python-export.md`
- Design: `docs/ui-conventions.md` (DEC-0008)
- Architecture: DEC-0045 (TASK-0070)
- Discovery: CodeMirror Python is already a dependency (TASK-0055).
- Clarifications: none

## Expected Outputs

- Panel component, header and palette entries, locale keys (en, vi)
- E2E test

## Implementation Notes

- Fetch the text once per version; find the node's lines from the markers TASK-0070 writes.
- Highlight with a CodeMirror line decoration in theme tokens, no hard-coded colours.

## Constraints

- shadcn components and theme tokens; en and vi keys identical; no literal UI text; DEC-0008 review checklist.

## Dependencies

- TASK-0070.

## Acceptance Criteria

- The panel shows the code of the open version; selecting a node highlights its function; Copy and Download work;
  viewers can open it; imported repositories have no such option.
- `npx tsc -b`, lint, vitest, build and e2e pass.

## Validation Plan

- E2E as in scope; manual check in light and dark themes, narrow window.

## Assumptions

- None.

## Open Questions

- None.

## Activity Log

- 2026-10-22: planned from REQ-0043.

## Handoff Notes

- TASK-0072 takes the handbook screenshot of this panel.
