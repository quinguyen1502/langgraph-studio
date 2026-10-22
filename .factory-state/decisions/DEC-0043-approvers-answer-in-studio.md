# Decision Record

## Metadata

- Project: superstep
- Decision ID: DEC-0043
- Status: Accepted
- Owner: Thái Quí Nguyễn
- Created: 2026-10-21
- Updated: 2026-10-21
- Related Requirements: REQ-0041
- Related Architecture: DEC-0013 (human in the loop), DEC-0019 (approval channels), DEC-0023 (RBAC and sharing)
- Related Tasks: TASK-0065, TASK-0066

## Context

DEC-0013 rule 1 lets only the run owner see and answer a waiting run in the studio. DEC-0019 added approvers: people
named by e-mail on a Human node who may press the buttons of a channel message. They have no way to find or answer the
request in the studio, and a Human node without a channel cannot name approvers at all. REQ-0041 asks for one inbox
of every approval waiting on a user, owner or approver.

## Decision

1. **Who may answer a waiting step.** The run owner, and the approvers of the waiting Human node. Approvers are the
   node's `data.approval.approvers` e-mails, resolved to studio users when the run starts waiting, plus anyone added by
   an escalation (TASK-0066). Everyone else gets `RUN_NOT_FOUND`, as before.
2. **What an approver sees.** Only the request: workflow name, step label, question, run owner, waiting since, the
   channel the request went to, and the deadline. Not the workflow, the run trace, the input or the state. "Open run"
   is offered only to users who may already read the run (its owner, and the workflow's owner or an admin).
3. **Where.** The Approvals inbox (`GET /api/approvals/inbox`, `POST /api/approvals/inbox/{run_id}`). The editor's
   Human panel, `GET /api/runs/pending`, the WebSocket resume and `POST /api/runs/{id}/cancel` stay owner only.
4. **One waiting step row per pause** (`approval_waits`, with its approvers in `approval_wait_approvers`). It is written
   when a run pauses at a Human node, with or without a channel, and closed when the wait ends. The inbox reads it, and
   it is the single gate for "first answer wins": the editor, a channel button and the inbox each close it with a
   compare-and-set, and the loser is refused (`RUN_NOT_WAITING` in the editor, `APPROVAL_ALREADY_DECIDED` elsewhere).
5. **An inbox answer resumes the run like a channel answer.** It queues the `resume` job with
   `by: {"channel": "studio", "user_id": …}`. The run stays its owner's and uses the owner's credentials and
   resources. Open channel requests are closed and their messages edited, and the Audit log records the answer with
   kind `studio`.
6. **Approvers on every Human node.** The approvers field no longer depends on choosing a channel.

## Rationale

- Approvers were already trusted to decide through a channel. Answering the same step in the studio gives them no new
  power, and without the trace or state they learn no more than the channel message tells them.
- A table of waiting steps keeps the inbox query cheap and portable (no JSON queries over checkpoints), and gives one
  place for the compare-and-set and, later, the deadline columns.
- Reusing the resume job keeps one path for every answer that does not come from the editor's open WebSocket.

## Alternatives Considered

- **Share the workflow with approvers.** Gives them far more than one decision. Rejected.
- **Read approvers from each waiting run's checkpoint.** Needs a scan and JSON parsing of every waiting run per
  request, and gives no row to compare-and-set. Rejected.
- **Resume in the request thread.** Duplicates the worker's resume path and blocks the HTTP request for the whole
  segment. Rejected.

## Consequences

- An inbox answer needs the job worker (`STUDIO_WORKER`, on by default), as channel answers already do.
- Runs that were already waiting before the migration have no waiting step row: they keep working from the editor and
  the channel, but do not show in the inbox.
- DEC-0013 rule 1 points here.
