# Decision Record

## Metadata

- Project: superstep
- Decision ID: DEC-0053
- Status: Accepted
- Owner: Thái Quí Nguyễn
- Created: 2026-10-23
- Updated: 2026-10-23
- Related Requirements: REQ-0048
- Related Tasks: TASK-0084, TASK-0085

## Decision

1. `access`: `studio` (phase 1: signed-in users with the workflow's run right). `anonymous` and `signed_in` are
   reserved and refused with `CHAT_ACCESS_NOT_AVAILABLE` until phase 2.
2. `steps`: what a visitor sees of a run: `none`, `labels` (default: node, label, type, status) or `full` (plus
   duration, input, output, errors). `GET /api/chat/sessions/{sid}?view=visitor` applies it; builders (`view=builder`,
   the studio default) always get `full`. The Chat tab can preview the visitor view.
3. Settings are read with the run right and changed with the share right (as for chat triggers).
