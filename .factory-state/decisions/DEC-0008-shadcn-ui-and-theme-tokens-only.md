# Decision Record

## Metadata

- Project: langgraph-studio
- Decision ID: DEC-0008
- Status: Accepted
- Owner: Thái Quí Nguyễn
- Created: 2026-10-16
- Updated: 2026-10-16
- Related Requirements: REQ-0001
- Related Architecture: ARCH-0001
- Related Tasks: TASK-0016 (first application), all future UI tasks

## Context

The owner reviewed the run trace timeline (TASK-0016) and required that the UI strictly follow shadcn/ui. An audit found hand-built widgets: a native checkbox, custom collapsible JSON toggles, plain buttons and alert divs. It also found hard-coded Tailwind palette colours (emerald, amber, sky, violet, orange, teal, zinc, `text-white`) in the trace UI, editor, list, auth and import dialog.

## Decision

Project-wide UI rule: **use shadcn/ui components and theme tokens only; no hard-coded colours; new status colours are added as shadcn-style CSS variables** (`--success`, `--warning`, `--info` plus their `-foreground` pairs, defined for light and dark). The full rules are in `docs/ui-conventions.md`, and `AGENTS.md` and `project.md` point to it.

## Consequences

- Node-type chips no longer use colour; they rely on their icons and `bg-muted`/`bg-secondary`.
- Badge gains `success` and `warning` variants.
- PR reviews check the conventions with the grep in `docs/ui-conventions.md`.

## Approval

- Approved By: Thái Quí Nguyễn (owner), 2026-10-16
