# Task

## Metadata

- Project: superstep
- Task ID: TASK-0065
- Status: todo
- Owner: Thái Quí Nguyễn
- Created: 2026-10-21
- Updated: 2026-10-21
- Requirement IDs: REQ-0041
- Design IDs: none (UX direction set in REQ-0041)
- Architecture IDs: DEC-0009, DEC-0013, DEC-0019, DEC-0043 (to write in this task)

## Objective

Give every user one Approvals inbox that lists the runs waiting on them, as owner or as a listed approver, and lets
them answer in place. Record who may answer from the studio in DEC-0043.

## Scope

### In Scope

- **DEC-0043 Approvers answer from the studio.** Amends DEC-0013 rule 1: the run owner and the people listed as
  approvers of the waiting node (escalation included, TASK-0066) may see and answer that step. An approver who is not
  the owner sees only the request (workflow name, step, question, deadline), not the workflow, the trace or the
  state. DEC-0013 gets a pointer to DEC-0043.
- **Waiting steps table.** A new model and migration for one row per waiting step: run, node, owner, approvers (studio
  user ids, resolved from the node's e-mail list when the run starts waiting), status (`waiting` / `closed`), created.
  - Written when a run starts waiting at a Human node, for every Human node, with or without a channel.
  - Closed when the run is answered, cancelled, expires, fails or finishes.
  - The inbox reads this table, so it does not parse every waiting run's checkpoint.
  - TASK-0066 adds the deadline columns to the same table.
- **API** (`backend/app/api/routes/approvals.py`, service in `approval_service.py` or a new `inbox_service.py`, repo in
  `repositories/approvals.py`):
  - `GET /api/approvals/inbox`: the user's waiting steps, owner or approver, each with workflow name, step label,
    question, owner e-mail when not the user, waiting since, channel kind where the request was sent, and
    `can_open` (the user may open the workflow).
  - `POST /api/approvals/inbox/{run_id}` `{response}`: answer the step. Same checks and effects as answering in the
    editor: `RUN_RESPONSE_INVALID`, `RUN_NOT_WAITING`, `APPROVAL_ALREADY_DECIDED`; closes channel requests and edits
    their messages (`close_run(rid, "answered")`); Audit log entry of kind `studio`; queues the resume job.
  - Someone who is neither owner nor approver gets `RUN_NOT_FOUND`.
  - `GET /api/runs/pending` stays for API users (owner only, unchanged).
- **Resume as an approver.** `RunService.plan_resume` accepts an approver for the waiting step, through the inbox route
  only. The resumed run still belongs to its owner and uses the owner's credentials and resources, as a channel answer
  does today.
- **Approvers on studio-only nodes.** `components/human-approval-settings.tsx` shows the approvers field for every
  Human node, not only once a channel is chosen. Help text says approvers answer from the channel and the inbox.
- **Inbox page** `frontend/src/pages/Approvals.tsx` at `/approvals`:
  - rows: workflow, step, question, owner (when not the user), waiting since, channel logo (`ChannelLogo`);
  - Approve, Reject, and a text reply in place. Share the answer controls with `human-panel.tsx` instead of copying
    them;
  - "Open run" only when `can_open`;
  - empty state with a short explanation;
  - refresh every 30 s and on window focus;
  - order: longest waiting first (TASK-0066 puts the nearest deadline first).
- **Navigation.** A header entry to the inbox. `pending-badge.tsx` counts the inbox and opens `/approvals`.
  `pending-runs.tsx` on the Workflows page becomes a short link to the inbox with the count, or is removed; pick one and
  keep a single list.
- **Docs.** Handbook (en, vi): a page for the Approvals inbox, and the Human node page says approvers can answer from
  it. Screenshots. API docs for the two routes.

### Out Of Scope

- Deadlines, reminders and escalation (TASK-0066).
- Bulk answers, delegation, filters beyond what the list needs.
- Push or real-time updates; polling is enough.

## Inputs

- REQ-0041, DEC-0013, DEC-0019, DEC-0037, DEC-0023 (sharing: who "can open" a workflow).
- `backend/app/services/run_service.py` (`pending`, `waiting_run`, `plan_resume`, `record`),
  `approval_service.py` (`on_waiting`, `_decide`, `close_run`, `decided_elsewhere`), `services/access.py`.
- `frontend/src/components/pending-runs.tsx`, `pending-badge.tsx`, `human-panel.tsx`, `human-approval-settings.tsx`,
  `approvals/channel-logo.tsx`.

## Related Artifacts

- Requirements: `.factory-state/artifacts/REQ-0041-approval-deadlines-and-inbox.md`
- Design: none
- Architecture: `docs/backend-architecture.md` (DEC-0009), `docs/ui-conventions.md` (DEC-0008)
- Decisions: DEC-0013, DEC-0019, DEC-0023, DEC-0037; DEC-0043 (new)
- Discovery: the approvers field is hidden until a channel is chosen; `RunService.pending` is owner only.
- Clarifications: none

## Expected Outputs

- `.factory-state/decisions/DEC-0043-approvers-answer-in-studio.md`; DEC-0013 points to it
- Model, repository and Alembic migration for waiting steps
- Inbox routes and service; tests
- `frontend/src/pages/Approvals.tsx`, route, header entry, badge change, shared answer controls
- Human node settings: approvers for every node
- en/vi locale keys; handbook pages and screenshots (en, vi)

## Implementation Notes

- One source of truth for "who may answer": the waiting step's approvers plus the owner. Channel requests keep their
  own `approvers` column for the button check; both are filled from the same resolved list.
- Resolve approver e-mails to user ids once, when the step is written. Unknown e-mails are dropped, as the channel
  request does today.
- Write and close waiting steps where `RunService.record` already hands `waiting` / final statuses to
  `ApprovalService` (`on_waiting`, `close_run`), so every path that ends a wait closes the row.
- Answering as an approver must not let them start, cancel or read the run in other ways.

## Constraints

- Layers (DEC-0009); SQLAlchemy + Alembic, no raw SQL; `tests/test_layers.py` passes.
- Envelope and central error handlers; any new error code in `CATALOG`, `docs/api-errors.md` and both locales.
- shadcn and theme tokens; en/vi keys identical; no UI text in components.
- SQLite and Postgres, with and without Redis.

## Dependencies

- None. TASK-0066 depends on this task.

## Acceptance Criteria

- A waiting step row is written for every run that pauses at a Human node and closed on every way the wait ends.
- `GET /api/approvals/inbox` returns the user's own waiting steps and those they are an approver of, and nothing else.
- An approver can answer from the inbox: the run resumes on the matching branch under its owner, the channel request is
  closed and its message edited, and the Audit log has the entry.
- The first answer wins across inbox, editor and channel; later ones get the existing codes.
- A user who is neither owner nor approver gets `RUN_NOT_FOUND` from the inbox route and cannot read the run.
- `can_open` is false, and "Open run" hidden, for an approver who cannot open the workflow.
- The approvers field shows on studio-only Human nodes.
- The header badge counts the inbox and opens `/approvals`; the Workflows page has no second copy of the list.
- DEC-0043 exists and DEC-0013 points to it.
- pytest (SQLite and Postgres), `npm run build`, lint, vitest and e2e pass; the handbook builds in en and vi.

## Validation Plan

- pytest: waiting step lifecycle (answered, cancelled, expired, error, finished); inbox listing for owner, approver and
  stranger; answer as approver; race between inbox and channel answer; layer test.
- E2E: an approver account answers a run from `/approvals`; the owner's badge count drops; approvers field on a
  studio-only node.
- `docs/ui-conventions.md` checklist.

## Assumptions

- Approvers have studio accounts (REQ-0041).

## Open Questions

- None.

## Activity Log

- 2026-10-21: planned from REQ-0041.

## Handoff Notes
