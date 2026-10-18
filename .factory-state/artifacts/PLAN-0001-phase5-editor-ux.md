# Plan

## Metadata

- Plan ID: PLAN-0001
- Phase: 5 — Editor UX
- Tasks: TASK-0023 → TASK-0028 (REQ-0013 … REQ-0018)
- Date: 2026-10-17
- Delivery: one stacked draft PR per task into `develop` (0023 ← 0024 ← … ← 0028)

## Order and dependencies

| # | Task | Builds on | Main pieces |
|---|---|---|---|
| 1 | TASK-0023 hotkeys + cheat sheet | — | `lib/shortcuts.ts` registry, `useShortcuts`, `ShortcutCheatsheet`, `lib/graph-ops.ts`, vitest |
| 2 | TASK-0024 undo/redo | 0023 registry + graph-ops | `lib/history.ts` reducer (coalescing, cap 100), `useGraphHistory`, toolbar buttons |
| 3 | TASK-0025 template library | — (backend) + editor | `templates` table + migration, TemplateService/Repository, sanitiser shared with export, gallery dialog, save-as, import/export |
| 4 | TASK-0026 copy/paste/duplicate | 0023 + 0024 | versioned clipboard payload in `lib/clipboard.ts`, Mod+C/X/V/D, one undo step per paste |
| 5 | TASK-0027 auto-layout | 0024 | `lib/layout.ts` (dagre, LR/TB, real node sizes), toolbar + Shift+L, one undo step |
| 6 | TASK-0028 command palette | registry, add-node, layout | shadcn Command (cmdk) dialog, Mod+K app-wide, actions/nodes/workflows/settings |

## Shared rules
- Every editor action is a registry entry, so the cheat sheet, key handler and palette never drift.
- Graph changes go through pure functions (`lib/graph-ops.ts`, `lib/layout.ts`, `lib/clipboard.ts`) with vitest unit tests; React only wires them.
- Strict shadcn, en+vi, envelope + English codes for the template API; deletes use ConfirmDeleteDialog (UI-only, DEC-0025).
- Tests per task: vitest units, Playwright e2e; backend pytest on SQLite + Postgres for TASK-0025; screenshots in 4 variants.
