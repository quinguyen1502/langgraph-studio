# Decision

## Metadata

- Decision ID: DEC-0031
- Status: Accepted (implementation in review)
- Date: 2026-10-17
- Related: TASK-0028, REQ-0018, DEC-0026, PLAN-0001

## Decisions
- **shadcn Command** (`components/ui/command.tsx`, new dependency `cmdk`) in a dialog, mounted once at the app root; **Mod+K** is a registry shortcut (`palette`, allowed in inputs) so it is in the cheat sheet. It is ignored on the login/register pages and while another modal is open.
- **Pages contribute commands** through a tiny external store (`lib/palette.ts`: `registerCommands(key, list)` → unregister, `usePaletteCommands`), so no provider is needed. The editor registers:
  - every registry action it handles (label from `shortcuts.actions.*`, its key shown; actions that can't run now are disabled, e.g. Stop when nothing runs, Undo with no history);
  - **Add node** for each type except Start/End (placed at the view centre, nudged off existing nodes, selected, one undo step);
  - **Jump to node** (selects it and zooms the view to it).
  The editor re-registers only when the visible content changes; runs read the latest closures through a ref.
- **Palette-owned groups:** **Open workflow** (fetched when opened, current one excluded, max 50) and **Go to** (workflow list, New workflow → `/workflows?new=1` opens the template gallery, every settings section the user may see, using `SECTIONS` and permissions).
- **Search:** cmdk's fuzzy scorer over label + hint + keywords + id, so English ids (`retriever`, `cheatsheet`, `mcp`) also match in the Vietnamese UI.
- Running a command first closes the dialog (focus returns) and then runs it.

## Consequences
- Editor actions appear only in the editor. Workflow search is client-side over the list API (fine for current sizes; server search can be added later).
