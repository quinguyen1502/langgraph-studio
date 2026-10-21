# Requirement

## Metadata

- Project: superstep
- Requirement ID: REQ-0041
- Status: Accepted (owner, in chat, 2026-10-21)
- Owner: Thái Quí Nguyễn
- Created: 2026-10-21
- Updated: 2026-10-21
- Source: owner request in chat, 2026-10-21. Asked for feature ideas, the owner chose proposals 1 and 2: deadlines and
  reminders on the Human node, and one inbox for every approval waiting on a user.

## Summary

- A Human node can have a **deadline**: remind the approvers while it waits, and when time runs out, reject, approve or
  hand the request to other people.
- An **Approvals inbox** page lists every run waiting on the signed-in user, as owner or as a listed approver, across
  all workflows. The user answers from the list.

## Problem Or Opportunity

- A waiting run only ends when someone answers it or when the global wait limit passes (`STUDIO_WAIT_TTL`, 7 days by
  default), when it becomes `expired` and stops. Channel buttons expire after `STUDIO_APPROVAL_TTL` (24 hours) with no
  reminder. A process such as a refund or a leave request needs its own time limit and a defined outcome, not a silent
  expiry a week later.
- Only the run owner sees waiting runs in the studio: a card on the Workflows page and a header badge, each opening the
  editor to answer. A listed approver can answer only through the channel message. If they miss the message, or the
  node has no channel, they have no way to find or answer the request.

## Scope

### In Scope

- **Deadline settings on the Human node** (`data.deadline`, optional):
  - `after`: how long the node waits, in minutes, hours or days (for example `30m`, `4h`, `2d`);
  - `remind_every` (optional): repeat a reminder at this interval while the node waits, at most 5 reminders;
  - `on_timeout`: `reject`, `approve` or `escalate`;
  - `escalate_to`: e-mail addresses of studio users, required when `on_timeout` is `escalate`.
- **Reminders.**
  - On a channel node, a reminder is a new message on the same channel and target with new buttons. The previous
    message is edited to say a reminder was sent, and its buttons stop working.
  - The run owner and the listed approvers also get an in-app notification (the bell), and an e-mail when their
    notification settings ask for it. On a studio-only node, the notification is the only reminder.
- **Timeout.**
  - `reject` / `approve`: the run resumes as if that answer had been given, so the workflow's branches work unchanged.
    The trace and the Audit log record the answer as given by the deadline, not by a person.
  - `escalate`: the request goes to the `escalate_to` people, on the same channel when the node has one, and in their
    inbox. They become approvers of this request. The owner and the first approvers can still answer. The escalated
    request waits the same `after` again; when that passes too, the run is rejected. Escalation happens once.
- **Channel buttons expire at the deadline** when it comes before `STUDIO_APPROVAL_TTL`.
- **Approvals inbox** at `/approvals`:
  - lists waiting runs the user owns and runs where the user is a listed approver of the waiting node (escalation
    included);
  - each row shows the workflow, the step, the question, the run owner (when it is not the user), waiting since, the
    deadline or "overdue", and the channel logo where the request was sent;
  - each row answers in place: Approve, Reject, or a text reply, like the editor's Human panel;
  - "Open run" opens the editor on that run, shown only when the user can open the workflow;
  - nearest deadline first, then the longest waiting; refreshes every 30 seconds and on window focus, like the header badge.
- **Navigation.** The header badge counts the inbox and opens it. The Workflows page card links to the inbox instead of
  listing runs a second time.
- **Approvers on studio-only nodes.** The approvers field shows for every Human node, not only for channel nodes, so a
  studio-only node can name who answers it from the inbox.
- **Answering from the inbox** has the same effect as answering in the editor: the run resumes, open channel requests
  are closed and their messages edited, the Audit log gets an entry, and the first answer wins.
- **Decision.** A new decision record (DEC-0043) amends DEC-0013 rule 1 (owner only): a listed approver may see and
  answer the waiting step of a run from the inbox, without access to the workflow or the run trace.
- **Templates.** The six built-in templates with a channel get a deadline that suits the process (for example the
  leave request waits 2 days with a daily reminder, then is rejected).
- **Docs.** The handbook (en, vi) explains deadlines on the Human node and the Approvals inbox, with screenshots.
  `docs/api-errors.md` and the API docs cover any new route.

### Out Of Scope

- Escalation chains (more than one escalation), or escalating to a team or a role.
- Business hours, holidays, or time zones for deadlines. Durations are wall-clock time.
- Deadlines on anything other than the Human node.
- Reassigning or delegating a request by hand from the inbox.
- Bulk approve or reject several rows at once.
- Push notifications to a phone. Reminders use the channels and notifications that already exist.

## Stakeholders Or Users

- Approvers named on a Human node, who today see requests only in the channel.
- Workflow owners who build approval processes and need them to end on time.
- Admins who read the Audit log.

## Current Context

- Human node: `backend/app/engine/nodes.py` (`t == "human"`, raises `Interrupt`), DEC-0013, REQ-0003, TASK-0006. The run
  is stored with status `waiting` and a checkpoint; `RunService.plan_resume` resumes it, owner only.
- Waiting limits: `config.wait_ttl()` (`STUDIO_WAIT_TTL`, 7 days, `RunService.expire_waiting`) and
  `config.approval_ttl()` (`STUDIO_APPROVAL_TTL`, 24 hours, the channel token expiry).
- Channel requests: `backend/app/services/approval_service.py` (`on_waiting`, `_request`, `_decide`, `close_run`),
  model `ApprovalRequest` (`approvers` JSON of user ids), DEC-0019, DEC-0037. The node's approvers are e-mail addresses
  in `data.approval.approvers`.
- Periodic work: `RunWorker.maintain` runs `promote_due`, schedules (`ScheduleService.fire_due`) and the job reaper
  every second. Scheduled runs are DEC-0036.
- Waiting list: `GET /api/runs/pending` (`RunService.pending`, owner only), shown by
  `frontend/src/components/pending-runs.tsx` (Workflows page) and `pending-badge.tsx` (header).
- Answering in the editor: `frontend/src/components/human-panel.tsx`.
- Notifications: `backend/app/services/notification_service.py` (`run_waiting`, `run_expired`, bell + optional e-mail).
- Human node settings: `frontend/src/components/human-approval-settings.tsx`. The approvers field shows only once a
  channel is chosen.
- Channel logos: `frontend/src/components/approvals/channel-logo.tsx` (REQ-0040, DEC-0042).

## Desired Behavior

- An author sets "Wait 4h, remind every 1h, then reject" on a Human node. A run waits there: after each hour the channel
  gets a new message and the approvers get a notification. After 4 hours with no answer the run continues on its
  `rejected` branch, and the trace shows "Rejected by deadline".
- With "then escalate to boss@example.com", after 4 hours the boss gets the request in the channel and in their inbox.
  After 4 more hours with no answer, the run is rejected.
- A listed approver opens **Approvals** and sees the request with its question and deadline. They click Approve; the
  run resumes, the channel message changes to "Approved by …", and the row leaves every inbox.
- A user with nothing to answer sees an empty inbox with a short explanation.

## Business Rules

- Only the run owner and the listed approvers (escalation included) may see or answer a request. Everyone else gets
  `RUN_NOT_FOUND`, as today.
- An approver who is not the owner sees only what the request shows (workflow name, step, question, deadline). They do
  not get the workflow, the run trace or the state.
- One answer per waiting step: the first answer wins, whether it comes from a channel, the editor, the inbox or the
  deadline. Later answers are refused with the existing codes (`APPROVAL_ALREADY_DECIDED`, `RUN_NOT_WAITING`).
- A deadline must be shorter than `STUDIO_WAIT_TTL` when that is set. The validator reports a longer one.
- Deadlines and reminders fire once each, also with several workers and after a restart.
- Every reminder, timeout and escalation is written to the Audit log.

## Constraints

- Backend layers (DEC-0009): routers → services → repositories; SQLAlchemy models and an Alembic migration for any new
  table or column; no raw SQL. `tests/test_layers.py` passes.
- Deadlines are checked by the existing worker maintenance loop, not a new process or scheduler.
- New error codes, if any, go in `CATALOG`, `docs/api-errors.md` and both locales.
- shadcn components and theme tokens; en and vi locale keys identical; no UI text in components.
- Works on SQLite and Postgres, with and without Redis.
- Mock mode: deadlines and the inbox work with no API key and no connected channel.

## Acceptance Criteria

- A Human node saves and validates `deadline` (`after`, `remind_every`, `on_timeout`, `escalate_to`); invalid values
  and a deadline longer than `STUDIO_WAIT_TTL` are reported.
- With a short deadline in tests, a waiting run gets its reminders on time, at most 5, each as a channel message (when
  the node has a channel) and a notification.
- On timeout, `reject` and `approve` resume the run on the matching branch; the trace and the Audit log name the
  deadline as the source.
- `escalate` sends the request to the listed people, adds them as approvers, waits once more and then rejects.
- Channel buttons stop working at the deadline and after a reminder replaces their message.
- Two workers sweeping at the same time fire each reminder and each timeout once.
- `/approvals` lists the user's own waiting runs and the runs they are a listed approver of, and nothing else.
- Approve, Reject and a text reply from the inbox resume the run, close the channel request and edit its message.
- An approver who cannot open the workflow sees no "Open run" link and gets `RUN_NOT_FOUND` for the run itself.
- The header badge counts the inbox and opens it.
- The approvers field shows on studio-only Human nodes.
- DEC-0043 exists and DEC-0013 points to it.
- Backend tests cover deadlines, reminders, escalation, concurrency and inbox access. e2e covers the inbox and the
  deadline settings.
- The handbook pages (en, vi) are updated, and both builds pass.

## Edge Cases

- The run is answered, cancelled or expires between two sweeps: nothing fires for it afterwards.
- The workflow is edited while a run waits: the deadline of the run's own snapshot applies, not the new graph.
- A loop that comes back to the same Human node: the deadline starts again for the new wait.
- Parallel branches waiting at more than one Human node: each node keeps its own deadline. The task confirms how this
  fits the existing resume of several waiting nodes.
- An escalation address with no studio account: it is skipped and the Audit log records it; with no valid address left,
  the timeout rejects at once.
- A channel that fails to send a reminder: the run keeps waiting, the Audit log records `send_failed`, and the deadline
  still applies.
- A deadline that has already passed when the worker starts after downtime: it fires on the first sweep, once.
- An approver is removed from the node after the request was sent: the request keeps the approvers it was sent with.

## Assumptions

- The defaults above (at most 5 reminders, one escalation, then reject) are acceptable to the owner.
- Approvers named by e-mail already have studio accounts; this requirement does not invite new users.

## Open Questions

- None. The owner accepted the requirement and its defaults on 2026-10-21.

## Related Artifacts

- REQ-0003 human in the loop, DEC-0013 (`.factory-state/decisions/DEC-0013-human-in-the-loop.md`), TASK-0006
- REQ-0034 more approval channels, DEC-0019, DEC-0037
- REQ-0033 scheduled runs, DEC-0036 (worker maintenance loop)
- REQ-0040 channel templates and logos, DEC-0042
- `frontend/src/components/pending-runs.tsx`, `pending-badge.tsx`, `human-panel.tsx`, `human-approval-settings.tsx`
- Handbook: `handbook/docs/*/guide/` (Human node), `handbook/docs/*/operate/channels.md`
