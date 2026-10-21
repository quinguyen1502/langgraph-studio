# Task

## Metadata

- Project: superstep
- Task ID: TASK-0066
- Status: todo
- Owner: Thái Quí Nguyễn
- Created: 2026-10-21
- Updated: 2026-10-21
- Requirement IDs: REQ-0041
- Design IDs: none (UX direction set in REQ-0041)
- Architecture IDs: DEC-0009, DEC-0013, DEC-0019, DEC-0036, DEC-0043

## Objective

Let a Human node set a deadline: remind the approvers while it waits, and when time runs out, reject, approve or
escalate once to other people.

## Scope

### In Scope

- **Node settings** `data.deadline` (optional): `after` (`<n>m|h|d`), `remind_every` (optional, same format),
  `on_timeout` (`reject` | `approve` | `escalate`), `escalate_to` (e-mails, required for `escalate`).
  - Validator: bad durations, `remind_every` not shorter than `after`, `escalate` without addresses, and `after`
    longer than `STUDIO_WAIT_TTL` (when set) are reported.
  - Template sanitize keeps `deadline` but drops `escalate_to` addresses, like approvers (TASK-0064).
  - UI: a "Deadline" section in the Human node settings, next to the approval channel, built from shadcn inputs and
    selects. Off by default.
- **Deadline columns** on the waiting steps table from TASK-0065 (migration): due at, next reminder at, reminders sent,
  escalated at. Filled from the run's own workflow snapshot when the step starts waiting.
- **Sweep.** `RunWorker.maintain` calls a deadline sweep each tick, next to `ScheduleService.fire_due`. Each reminder
  and each timeout is claimed with compare-and-set on the row, so it fires once with several workers and after a
  restart. A deadline already passed after downtime fires on the first sweep.
- **Reminder** (at most 5):
  - channel node: a new request message on the same connection and target with new buttons; the previous message is
    edited to say a reminder was sent and its request is superseded;
  - a `run_reminder` notification (bell, and e-mail per the user's settings) to the owner and the approvers;
  - Audit log `reminded`.
- **Timeout:**
  - `reject` / `approve`: queue the resume job with that response, recorded as by the deadline
    (`by: {"channel": "deadline"}`); trace event names the deadline; channel requests closed and edited; Audit log
    `timed_out`.
  - `escalate`: resolve `escalate_to` to users (unknown ones skipped and audited), add them to the step's approvers,
    send a new channel request when the node has a channel, notify them, set a new due time (`after` again), Audit log
    `escalated`. When the second due time passes, reject. With no valid address, reject at once.
- **Channel buttons** expire at `min(due at, now + STUDIO_APPROVAL_TTL)`.
- **Inbox** (TASK-0065): show the due time or "overdue" and order by the nearest due time first, then the longest
  waiting.
- **Templates.** The six built-in templates with a channel get a deadline that suits the process (for example leave
  request: 2 days, remind every day, then reject). `tests/test_templates.py` updated.
- **Docs.** Handbook (en, vi) Human node page: the deadline settings and what happens on timeout; the inbox page shows
  the due time; screenshots. `docs/api-errors.md` for any new code.

### Out Of Scope

- Escalation chains, teams or roles as targets.
- Business hours, holidays, time zones.
- Deadlines on other node types.

## Inputs

- REQ-0041, TASK-0065 (waiting steps table, inbox).
- `backend/app/services/run_worker.py` (`maintain`), `schedule_service.py` (`fire_due` pattern),
  `approval_service.py` (`_request`, `close_run`, `_update`), `notification_service.py` (`KINDS`, `run_event`),
  `run_service.py` (`plan_resume`, `expire_waiting`), `engine/validator.py`, `engine/templates.py` (`sanitize`).
- Channel message texts: `services/approval_channels/messages.py` (en, vi).

## Related Artifacts

- Requirements: `.factory-state/artifacts/REQ-0041-approval-deadlines-and-inbox.md`
- Design: none
- Architecture: `docs/backend-architecture.md` (DEC-0009)
- Decisions: DEC-0013, DEC-0019, DEC-0036, DEC-0037, DEC-0043
- Discovery: waiting runs expire globally after `STUDIO_WAIT_TTL` (7 days); channel tokens after
  `STUDIO_APPROVAL_TTL` (24 hours); neither reminds.
- Clarifications: none

## Expected Outputs

- Migration for the deadline columns; sweep in the service layer, called from `RunWorker.maintain`
- Validator, sanitize and Human node settings UI for `deadline`
- Reminder and timeout texts for channels, notifications and the trace (en, vi)
- Inbox due time and order
- Six built-in templates with deadlines
- Tests; handbook pages and screenshots (en, vi)

## Implementation Notes

- Keep the time source injectable (`now` argument), as `fire_due` does, so tests run without sleeping.
- The timeout answer goes through the same resume path as a channel decision, so the first-answer-wins rules apply
  unchanged.
- A loop back to the same Human node writes a new waiting step, so its deadline starts again.
- Parallel branches waiting at more than one Human node: confirm how resume of several waiting nodes works today and
  record the behaviour in the task's handoff notes.

## Constraints

- Layers (DEC-0009); SQLAlchemy + Alembic, no raw SQL; `tests/test_layers.py` passes.
- No new process or scheduler: the worker maintenance loop only.
- shadcn and theme tokens; en/vi keys identical; no UI text in components.
- SQLite and Postgres, with and without Redis. Mock mode works.

## Dependencies

- TASK-0065 (waiting steps table and inbox).

## Acceptance Criteria

- `deadline` saves, validates and survives template save without the escalation addresses.
- With a short deadline and an injected clock, reminders fire on time, at most 5, as channel messages (channel node)
  and notifications.
- `reject` and `approve` resume the run on the matching branch; trace and Audit log name the deadline.
- `escalate` reaches the listed people (channel and inbox), adds them as approvers, waits once more, then rejects.
- Channel buttons stop working at the deadline and when a reminder replaces their message.
- Two sweeps at once fire each reminder and timeout once; nothing fires for a run already answered, cancelled or
  expired.
- The inbox shows the due time and "overdue", nearest due first.
- The six channel templates carry deadlines and still run offline.
- pytest (SQLite and Postgres), `npm run build`, lint, vitest and e2e pass; the handbook builds in en and vi.

## Validation Plan

- pytest: duration parsing and validator; sweep with an injected clock (reminders, cap, reject, approve, escalate,
  unknown addresses, send failure, downtime catch-up); concurrency (two sweeps); interplay with answer, cancel and
  `STUDIO_WAIT_TTL`.
- E2E: set a deadline in the Human node settings; a run with a past due time is rejected on the next sweep and shows
  in the trace; inbox shows "overdue".
- `docs/ui-conventions.md` checklist.

## Assumptions

- The defaults in REQ-0041 (5 reminders, one escalation, then reject) stand.

## Open Questions

- None.

## Activity Log

- 2026-10-21: planned from REQ-0041.

## Handoff Notes
