# Decision

## Metadata

- Decision ID: DEC-0027
- Status: Accepted (implementation in review)
- Date: 2026-10-17
- Related: TASK-0024, REQ-0014, DEC-0026, PLAN-0001

## Decisions
- **What is recorded:** snapshots of the graph content: nodes (id, type, rounded position, settings without runtime `_` fields), edges (id, source, target, label, conditional) and the state schema. Selection, measurements and run status are never history steps.
- **Pure reducer** (`lib/history.ts`: `init/push/undo/redo`, capped at 100) with vitest tests. `useGraphHistory` watches the editor state, so every edit path is covered automatically (drop, connect, delete, inspector, schema, later paste and layout) without each one having to "record".
- **Coalescing:** consecutive changes with the same key inside 1 s merge. The keys are `data:<node>` (typing in one node's settings) and `state` (schema edits). Structure changes and moves never merge. While a node is being dragged, nothing is recorded, so one drag is one step.
- **Reset:** on load, version restore and ownership-transfer reload (where the unsaved baseline is taken).
- **Keys:** Mod+Z undo, Mod+Shift+Z / Mod+Y redo, plus toolbar buttons with disabled states. In text fields the native text undo is kept (graph undo only fires outside inputs).
- **Unsaved marker:** a header badge (warning token) compares the content with the saved snapshot, so undoing back to the saved state clears it.

## Consequences
- History is per editor session (no persistence; versions cover saved states). Viewers have no history controls.
