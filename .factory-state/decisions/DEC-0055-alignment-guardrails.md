# Decision Record

## Metadata

- Project: superstep
- Decision ID: DEC-0055
- Status: Accepted
- Owner: Thái Quí Nguyễn
- Created: 2026-10-23
- Updated: 2026-10-23
- Related Requirements: REQ-0049
- Related Architecture: DEC-0008 (UI conventions)
- Related Tasks: TASK-0086

## Context

Rows drifted because controls were sized by hand (`h-6`, `h-7`, `py-2`, `text-[10px]`) next to controls sized by
their variant, and mixed fonts were forced together with `leading-none`. Nothing caught it until a screenshot review.

## Decision

1. Sizing goes through shadcn variants only. Where a size was missing, the ui component gets a `cva` variant:
   Badge `size="sm"` (16px, 10px text) and TabsList `size="sm"` (28px, triggers follow through the list's
   `data-size`). Button already has `xs`/`sm`/`icon-*`; SelectTrigger has `sm`.
2. A row uses one size: the header controls are all 32px (the Input has no smaller size), so the header's text
   buttons and the approvals badge moved from `sm` (28px) to `default`.
3. The lint check is a small TypeScript-AST script (`frontend/scripts/check-ui-classes.mjs`), not an oxlint rule:
   oxlint has no custom-rule API we can ship without a JS plugin build step, and the script resolves which JSX tags
   come from `@/components/ui/*` imports. It runs as `npm run lint:ui` inside `npm run lint` (factory verify) and on
   CI (new `npm run lint` step in the frontend job), and exits 1 on a hit.
4. Exempt by design: Skeleton, ScrollArea, Separator and ResizablePanel, whose size is their content (shadcn sizes
   them by class). Everything else needs `/* ui-class-ok: <reason> */` on the element; an empty reason does not count.
5. Baselines are measured, not inferred from boxes: the e2e helper wraps the first text run and a zero-size
   inline-block probe in one inline box (so a flex parent cannot make the probe its own flex item) and reads the
   probe's top.

## Consequences

- New hand-sized controls fail `npm run lint`; a deliberate exception is visible in review with its reason.
- The editor header buttons are 4px taller.
