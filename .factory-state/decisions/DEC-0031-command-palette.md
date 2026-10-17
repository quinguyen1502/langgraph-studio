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

## Follow-up (2026-10-17 16:20 UTC+7, approved by the owner): decluttered editor header
- The header shows only the workflow name, the Unsaved / view-only badges, **Save**, **Run** (+ **Stop** while running) and **Undo/Redo**. Everything else lives in one shadcn `DropdownMenu` behind a ⋯ (`MoreHorizontal`) icon button with a tooltip.
- Menu sections, with separators between them:
  - **Arrange:** Tidy up, Left→right, Top→bottom, Fit view.
  - **Workflow:** Versions, Save as template, Share, API / trigger, JSON.
  - **Help:** Command palette (shows Mod+K, so the palette is discoverable), Keyboard shortcuts.
  - **Danger:** Delete workflow, last, in the destructive variant. It opens the shared ConfirmDeleteDialog, extracted as `useDeleteWorkflow` and reused by the workflow list.
- Items show their registry shortcut (`DropdownMenuShortcut`).
- **Single source:** the menu is `menuSections()` over the same `PaletteCommand` list the editor registers with the palette (a command flagged `menu` appears in both).
- **Dialogs:** Share, Versions, API and Save as template accept `open` / `onOpenChange` (`useOpenState`). When controlled by the editor they render no trigger of their own.
- Menu items keep the old element ids (`share-btn`, `versions-btn`, `api-btn`, `save-template-btn`, `layout-btn`, `layout-lr/tb`, `shortcuts-btn`), so the tests only open the menu first.
