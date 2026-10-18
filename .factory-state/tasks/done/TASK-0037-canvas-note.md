# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0037
- Status: done
- Phase: canvas note
- Owner: Thái Quí Nguyễn
- Created: 2026-10-18
- Updated: 2026-10-18
- Requirement IDs: REQ-0025
- Design IDs:
- Architecture IDs:

## Objective

Add a non-executable note block to the flowchart.

## Scope

### In Scope

- A sticky on the canvas, added by right-clicking the chart, with the text edited on the sticky
- Validator, compiler, and Arrange ignoring the note as an executable node
- `--node-note`, `--node-note-foreground`, and `--node-note-muted` in light and dark

### Out Of Scope

- Inserting a note onto an edge or between two nodes
- Markdown, per-note colours, and a custom resize handle
- Typed-name confirmation when deleting a note

## Inputs

- `.factory-state/artifacts/REQ-0025-canvas-note.md`

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0025-canvas-note.md`
- UI conventions: `docs/ui-conventions.md`
- Decision: `.factory-state/decisions/DEC-0008-shadcn-ui-and-theme-tokens-only.md`
- Editor: `frontend/src/pages/Editor.tsx`
- Layout: `frontend/src/lib/layout.ts`
- Validator: `backend/app/engine/validator.py`
- Compiler: `backend/app/engine/compiler.py`

## Expected Outputs

- A note the author can place, edit, save, and delete on the canvas
- Validator and compiler tests, plus a layout test that the note does not move
- `note` added to the node-type list in `docs/ui-conventions.md`
- One sentence in `README.md` and `README.vi.md`

## Implementation Notes

- Store the body on `data.text`. Empty text is valid and shows the placeholder.
- Do not add the note to the palette, `INSERTABLE`, or `add:` command-palette entries. Add it from the canvas context menu at the click position.
- Draw no handles, so a note cannot be connected. A pasted edge that touches a note still fails validation and the message names the note.
- Skip note nodes in `compile_workflow` before `add_node`. Do not give them an outgoing-edge error.
- `layoutGraph` returns notes at their current positions and lays out the other nodes. A note sitting far from the graph must not change the anchor of Arrange.
- Add the three note tokens in `frontend/src/index.css` for `:root` and `.dark`, and map them in `@theme inline`. The sticky uses them on the paper. Graph nodes keep using `META`.
- Canvas delete stays `removeIds`. Do not use `ConfirmDeleteDialog`.
- Strings in `frontend/src/locales/en.json` and `vi.json` with the same keys.

## Constraints

- No new API route and no new error code. The engine does not import FastAPI.
- shadcn components and theme tokens. No hard-coded colours. No left accent bar.
- Branch `factory/task-0037-canvas-note` from `develop`. One Draft PR into `develop`. Do not merge until the owner asks.
- Pytest uses `/tmp/lgs-qa-venv`. Do not use `backend/.venv`. Frontend typecheck is `cd frontend && npx tsc -b`.

## Dependencies

- None. Independent of TASK-0036. Start from `develop`.

## Acceptance Criteria

- Same as REQ-0025.

## Validation Plan

- `cd backend && /tmp/lgs-qa-venv/bin/python -m pytest -q` for the validator and compiler tests that cover a loose note and an edge into a note, plus `tests/test_layers.py`
- `cd frontend && npx tsc -b` and the layout test (`npx vitest run` for `layout`)
- `git diff --check`
- In the browser, add a note, type text, save, reload, and confirm the text is back and Arrange did not move it

## Assumptions

- Small-task workflow. Designer and architect are skipped; the block follows the existing node card.
- `factory ready` does not exit 0 here. The owner asked for the task anyway. Do not install packages to clear that check.
- GitHub Actions fails from quota. Local tests are the evidence.

## Open Questions

- None

## Activity Log

- 2026-10-18: Owner asked for the task. REQ-0025 approved. Task filed in `todo`. Not started.
- 2026-10-18: Owner asked to implement. Branch `factory/task-0037-canvas-note` from `develop` (`831ad6e`). Task moved to `doing`. `factory ready` still does not exit 0 on this machine; the owner asked for the task anyway. No packages installed.
- 2026-10-18: Implemented in the working tree. Not committed. No pull request. Local checks: pytest 43 passed (`test_canvas_note`, `test_layers`, `test_api_envelope`, `test_core_hardening`, `test_compiler`); `npx tsc -b`; vitest layout 4 passed; `git diff --check`.
- 2026-10-18: Owner asked for a sticky added by right-click on the canvas, not a graph node in the palette. The chart UI follows that. The saved document still carries the sticky so a run can ignore it. Browser check: right-click adds it, palette and command palette do not, text survives save and reload, Arrange leaves it, delete does not ask for a name.
- 2026-10-18: Owner asked to finish the remaining steps. REV-0036 has no blocking findings. QA-0036 passed. Task set to done. Draft PR [#40](https://github.com/quinguyen1502/langgraph-studio/pull/40) into `develop`, then marked Ready. Not merged.

## Handoff Notes

- Ready PR #40 into `develop`: https://github.com/quinguyen1502/langgraph-studio/pull/40
- Do not merge until the owner asks.
- Do not stack another task on this branch.
