# Decision

## Metadata

- Decision ID: DEC-0026
- Status: Accepted (implementation in review)
- Date: 2026-10-17
- Related: TASK-0023, REQ-0013, PLAN-0001

## Decisions
- **One registry** (`frontend/src/lib/shortcuts.ts`): `{ id, keys[], group, allowInInputs }`. Combos are platform-neutral (`mod` = ⌘ on macOS, Ctrl elsewhere). The editor binds handlers by id (`useShortcuts`); the cheat sheet (and later the command palette) render from the same list, so they cannot drift.
- **Matching:** exact modifiers; digits by `code` (Shift+1 types `!`); punctuation by `key` (layout-aware `?`).
- **Typing rule:** in inputs, textareas, selects, comboboxes and contenteditable, only `allowInInputs` shortcuts fire (save, run, stop). While a modal dialog is open, the editor shortcuts are off (the dialog owns the keyboard).
- **Delete:** React Flow's built-in delete key is turned off. Our handler removes the selected nodes and edges through `lib/graph-ops.ts`, and Start/End are never removed (the inspector's delete button is hidden for them too). Imported (code) graphs stay read-only.
- **Keys:** save Mod+S, run Mod+Enter, stop Mod+. (Mod+. rather than Esc, which clears the selection), delete Del/⌫, select all Mod+A, fit Shift+1, zoom Mod+= / Mod+-, cheat sheet ? or Mod+/.
- **Unit tests:** vitest + jsdom were added to the frontend (`npm test`).

## Consequences
- No user remapping (out of scope). Browser-reserved combos (Mod+W/T/N) are avoided.
