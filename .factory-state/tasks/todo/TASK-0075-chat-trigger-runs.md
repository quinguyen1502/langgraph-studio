# Task

## Metadata

- Project: superstep
- Task ID: TASK-0075
- Status: todo
- Owner: Thái Quí Nguyễn
- Created: 2026-10-22
- Updated: 2026-10-22
- Requirement IDs: REQ-0044
- Design IDs: none (behaviour set in REQ-0044 and CLAR-0002)
- Architecture IDs: DEC-0009, DEC-0019, DEC-0046

## Objective

Start runs from Slack and Telegram messages that match a chat trigger, and answer in the thread: started, then the
result, the error or the waiting note. Refusals are answered to the sender only.

## Scope

### In Scope

- **Adapter interface** (`approval_channels/base.py`):
  - `handle_message(body) -> Optional[ChatMessage]`. A `ChatMessage` holds `team`, `place`, `is_dm`, the sender, the
    text without the bot mention, a dedupe key and a reply reference;
  - `reply(secrets, ref, text)` posts in the thread;
  - `reply_private(secrets, ref, sender, text)` answers the sender only: a Slack ephemeral message, a Telegram reply.
  - Slack and Telegram implement them. Bots' own messages, edits, joins and files give `None`.
- **Slack events** `POST /api/channels/events/slack` (no JWT):
  - it answers `url_verification` with the challenge;
  - it routes by `team_id` to the workspace's connection and verifies the signing secret and timestamp, as approval
    callbacks do;
  - it handles `app_mention` (in channels) and `message.im` (direct messages);
  - it replies 200 at once and queues the work;
  - Slack retries (`X-Slack-Retry-Num`) and repeated `event_id`s start nothing new.
- **Telegram:** the existing callback `POST /api/approvals/callback/telegram/{cid}` sends `message` updates to chat
  triggers and `callback_query` to approvals, after the same secret check.
- **Matching:** connection + place (a channel or group id, or `dm`) + the first word, case-insensitive, after the
  mention, a colon or spaces.
- **Checks, in order.** A message that fails a check gets a private refusal in the sender's language and an audit
  entry:
  - the trigger is on, and its creator still has the share right (else the trigger stops with a note);
  - the sender's account is linked and verified in that workspace (`ApprovalRepository.user_for`);
  - that studio user may run the workflow (`AccessService`, the run right);
  - the rate limit per sender and trigger (`STUDIO_CHAT_TRIGGER_RATE_LIMIT`, default as for API tokens);
  - the input size limit.
- **Runs:**
  - `source="chat"`, owned by the sender's studio user;
  - the input is the workflow's defaults plus `{input_field: text}`;
  - queued through the job queue like API runs;
  - stored with the trigger id, the sender's chat account and the reply reference (new run columns or a small
    `chat_run` table: the implementer picks one and records it in DEC-0046);
  - the trigger's `last_message` and `last_run_id` are updated.
- **Replies in the thread**, in the run owner's language (en, vi):
  - **Started:** "Started <workflow> · open run".
  - **Settled** (`RunService.settled`, the same hook as API callbacks, once per segment):
    - finished: the reply field's value, as text or compact JSON, shortened to the platform's limit;
    - error: the error message;
    - waiting: "waiting for approval at <node label>".
  - A resumed run that finishes later posts its result then.
  - The link goes to the run in the studio (`config.public_url()`).
- **Audit:** every started run and every refusal, as for approval callbacks.
- **Tests** `backend/tests/test_chat_trigger_runs.py`, with Slack and Telegram faked through `httpx.MockTransport`.
  They cover:
  - signature, timestamp and `url_verification`;
  - a duplicate `event_id` or retry gives one run;
  - command matching variants;
  - each refusal (unlinked, unverified, no run right, off, rate-limited, too large, workflow gone), private and
    audited;
  - the run gets `source`, owner and input;
  - started / finished / error / waiting replies, a waiting run that finishes later, and the reply field shortened;
  - Telegram buttons still decide approvals on the same webhook;
  - bots' messages and edits are ignored.

### Out Of Scope

- The editor dialog, the Channels page and the run history badge (TASK-0076).
- The handbook guide page (TASK-0077).
- Answering Human nodes by typing in the thread; conversations; files.

## Inputs

- TASK-0074 outputs (rows, service, DEC-0046).
- `services/approval_service.py` (`handle_callback`, `_connection`, audit), `api/routes/approvals.py`,
  `services/trigger_service.py` (`start`, rate limit, `run_result`), `run_service.py` (`settled`),
  `run_worker.py`, `identity_service.py`, `approval_channels/messages.py` (en, vi texts), `services/access.py`.

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0044-chat-triggers.md`
- Clarification: `.factory-state/artifacts/CLAR-0002-chat-triggers.md`
- Design: none
- Architecture: `docs/backend-architecture.md` (DEC-0009)
- Decisions: DEC-0019, DEC-0023, DEC-0046
- Discovery: none

## Expected Outputs

- The adapter methods (Slack, Telegram), the events route, Telegram dispatch, `ChatRunService` (or methods on the
  TASK-0074 service), run storage for the chat reference, a migration if columns are added
- Reply texts (en, vi) next to the approval texts
- `tests/test_chat_trigger_runs.py`
- DEC-0046 updated with the storage choice

## Implementation Notes

- Slack wants an answer in 3 s. The route verifies, dedupes and enqueues a `chat_message` job. The worker does the
  checks, starts the run and posts the "started" reply.
- Dedupe by `event_id` (Slack) or `update_id` (Telegram), with a unique key in the database so that two workers
  cannot both start a run.
- Reuse `run_result` for the reply content and the approval texts module for en/vi strings.

## Constraints

- Layers (DEC-0009); SQLite and Postgres.
- The reply never holds anything but the chosen field, the status, the node label and the run link.

## Dependencies

- TASK-0074.

## Acceptance Criteria

- A Slack mention or direct message, or a Telegram message, with a known command from a verified, permitted user
  starts exactly one `source="chat"` run owned by that user. Replays start nothing.
- The thread gets the started note and, when the run settles, the result, error or waiting note. A run that waits and
  later finishes posts the result.
- Each refusal is private to the sender, in their language, and audited. Stopped triggers record why.
- Bad signatures, stale timestamps and unknown workspaces are rejected. Telegram approval buttons keep working.
- pytest (SQLite and Postgres) and `tests/test_layers.py` pass.

## Validation Plan

- `pytest tests/test_chat_trigger_runs.py tests/test_chat_triggers.py`, the approval tests, the full suite, and
  Postgres in CI.

## Assumptions

- Slack's `app_mention` text starts with `<@BOTID>`. Telegram group messages to a bot use `/command` or a mention,
  with privacy mode as the bot owner set it. The handbook (TASK-0077) explains privacy mode.

## Open Questions

- None.

## Activity Log

- 2026-10-22: planned from REQ-0044.

## Handoff Notes

- None.
