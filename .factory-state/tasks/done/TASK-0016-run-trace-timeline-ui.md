# Task

## Metadata

- Project: wt-t
- Task ID: TASK-0016
- Status: todo
- Owner: Grok Bot (agent)
- Created: 2026-10-16
- Updated: 2026-10-16
- Requirement IDs: REQ-0001
- Design IDs:
- Architecture IDs: ARCH-0001

## Objective

Replace the cluttered raw-event Logs tab with a compact run trace timeline (LangSmith/Langfuse trace tree, n8n per-node I/O, Dify tracing cards) so a run can be understood and debugged per node.

## Scope

### In Scope

- Timeline: one row per node execution. Each row shows a status icon, the node name with a type icon, the duration, a waterfall bar relative to the run, and tokens when present.
- A run summary header: status, total time, step count, tokens.
- Errors highlighted.
- Row detail tabs: Input (state before), Output (node return), State diff (added/changed/removed), Raw event JSON.
- A collapsible JSON viewer with a copy button.
- Canvas ↔ timeline sync: clicking a node selects its latest row (repeated clicks cycle through iterations), and the selected row highlights its node.
- Loops show as separate rows labelled #2, #3, …
- Raw event stream behind a "Raw events" toggle.
- History replay uses the same timeline.
- Backend: `node_finished` carries `input` (state before), `node_type` and `iteration`.
- Backend: payloads are capped (16 000 JSON characters per field).
- Backend: runtime errors are attributed to the running node.
- Backend: per-run `recursion_limit` (`STUDIO_RECURSION_LIMIT`, default 25), so loops end quickly.

### Out Of Scope

- Real token accounting (shown only when events carry `tokens` or `usage`; the mock LLM has none)
- Nested sub-graph trace trees (TASK-0011)
- Input/state capture for imported-repo runs (runner events unchanged)

## Inputs

- `project-specs.md`
- `vision.md`
- `project.md`
- `roadmap.md`
- `backend/app/compiler.py`, `backend/app/main.py` (run events)
- `frontend/src/pages/Editor.tsx` (run panel)

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0001-mvp-baseline.md`
- Discovery: `.factory-state/artifacts/DISC-0001-project-context.md`
- Related tasks: TASK-0003 (base), TASK-0004 (runtime hardening)

## Expected Outputs

- `frontend/src/lib/trace.ts`, `components/run-trace.tsx`, `components/json-view.tsx`; Editor integration
- Backend event fields + tests; Playwright `e2e/trace.spec.ts`; screenshots `docs/screenshots/trace-*.png`; REV/QA records

## Constraints

- Preserve explicit technology approval statuses.
- No new dependencies; shadcn/Tailwind style with dark mode; the event protocol stays backward compatible (only additive fields)

## Dependencies

- TASK-0003 branch (PR #5): this branch is stacked on it

## Acceptance Criteria

- The Logs tab shows the summary and one row per node execution with a duration bar; errors are highlighted
- Clicking a row opens detail with Input/Output/State diff/Raw; the JSON viewer collapses and copies
- Clicking a canvas node selects the matching row; the selected row highlights the node
- Repeated executions show #2, #3; a looping workflow stops at the recursion limit with the error on the node row
- The Raw events toggle shows the raw stream; History replay renders the same timeline
- Backend tests, `npm run build`/`lint`, Playwright E2E pass; screenshots in docs/screenshots

## Validation Plan

- `cd backend && .venv/bin/python -m pytest -q`
- `cd frontend && npm run build && npm run lint && npm run e2e`
- `factory verify run --profile full`, `factory validate`

## Assumptions

- None

## Open Questions

- Should the recursion limit be configurable per workflow (TASK-0004)?

## Activity Log

- 2026-10-16: Created (owner request: Logs tab too cluttered). Phase 1, linked to REQ-0001. Moved todo -> doing on `factory/task-0016-run-trace-timeline-ui` (based on the TASK-0003 branch).
- 2026-10-16: Implemented the backend event fields, the trace UI and the E2E tests. Found that the default langgraph recursion limit (~10k) made loop runs emit about 20k events; added `STUDIO_RECURSION_LIMIT=25`.
- 2026-10-16: Moved doing -> review. REV-0004-task-0016, QA-0004-task-0016.
- 2026-10-16: Owner review: the UI must strictly follow shadcn/ui. Recorded DEC-0008 and `docs/ui-conventions.md`. Replaced custom widgets with shadcn Switch, Collapsible, Alert, Tooltip, Separator and Button, and hard-coded colours with the tokens `--success`, `--warning` and `--info`, across the whole app.
- 2026-10-16: Added node-type colour tokens (`--node-*`, DEC-0008 addendum) for the palette, canvas cards, config header and trace icons.

## Handoff Notes

- Branch `factory/task-0016-run-trace-timeline-ui`, PR base `factory/task-0003-harden-auth-login-and-workflow-list` (PR #5).
- Merge after #5, then retarget to `main`.
- Core-runtime hardening that touches run limits overlaps TASK-0004; coordinate `STUDIO_RECURSION_LIMIT` there.
