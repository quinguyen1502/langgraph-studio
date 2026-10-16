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

- Badge gains `success` and `warning` variants.
- PR reviews check the conventions with the grep in `docs/ui-conventions.md`.

## Approval

- Approved By: Thái Quí Nguyễn (owner), 2026-10-16

## Addendum (2026-10-16): node-type colour tokens

The owner wants node types to be easy to tell apart by colour again, using theme variables.

- Each node type (`start`, `llm`, `tool`, `condition`, `end`, `code`) has `--node-<type>`, `--node-<type>-foreground` and `--node-<type>-muted` in `:root` and `.dark`, registered in `@theme inline`. That makes classes such as `bg-node-llm-muted`, `text-node-llm` and `border-node-code` available.
- They are applied to palette chips, the accent stripe on canvas node cards, the config header and the trace timeline icons. Imported Code nodes keep a dashed `border-node-code/60` border.
- Node-type colours mean category only; statuses stay on `success`/`warning`/`destructive`.
- Approved by: Thái Quí Nguyễn (owner), 2026-10-16
