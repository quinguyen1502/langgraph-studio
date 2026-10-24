# Decision Record

## Metadata

- Project: superstep
- Decision ID: DEC-0054
- Status: Accepted
- Owner: Thái Quí Nguyễn
- Created: 2026-10-23
- Updated: 2026-10-23
- Related Requirements: REQ-0048, REQ-0041 (deadlines, inbox)
- Related Tasks: TASK-0084, TASK-0085

## Decision

1. Human node data `answered_by`: `visitor` (default) or `reviewer`; the validator refuses other values.
2. `visitor`: the chat shows the question as an answer form; the answer resumes the run over the run socket.
3. `reviewer`: the chat shows "waiting for approval"; the existing Approvals inbox (every Human node already writes a
   waiting step) and approval channels answer it. A chat answer is refused with `CHAT_ANSWER_BY_REVIEWER`.
4. Timeout: the node's existing `deadline` (REQ-0041) applies to both; when it fires, the run continues or ends and the
   chat shows that outcome. A run that expires (`STUDIO_WAIT_TTL`) or fails shows an error turn with its code.
   A new message while the run waits is `CHAT_RUN_WAITING`.
