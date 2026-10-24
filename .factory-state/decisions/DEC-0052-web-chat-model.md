# Decision Record

## Metadata

- Project: superstep
- Decision ID: DEC-0052
- Status: Accepted
- Owner: Thái Quí Nguyễn
- Created: 2026-10-23
- Updated: 2026-10-23
- Related Requirements: REQ-0048, REQ-0044
- Related Architecture: DEC-0046 (chat triggers), DEC-0009 (layers)
- Related Tasks: TASK-0084, TASK-0085

## Context

Slack/Telegram chat triggers already start one run per message and answer once per settled state (`chat_messages.replied`).
A web chat needs the same, plus a conversation, memory, streaming and settings.

## Decision

1. **The web chat is a chat trigger of kind `web`**: `channel_id = place = "web"`, `command` = the slug for the
   published page (default: the workflow id), `input_field` / `reply_field` / `enabled` as for other triggers, and the
   rest in a `settings` JSON (`access`, `messages_field`, `max_turns`, `steps`, `retention_days`). At most one per
   workflow; the Slack/Telegram trigger list leaves it out.
2. **Sessions and turns**: `chat_sessions` (workflow, trigger, `channel` studio|web|embed, owner or `visitor`, title,
   `updated` as the retention clock) and `chat_turns` (role, text, status, the waiting Human `node` and `answered_by`,
   error `code`, `attachments` reserved). Node steps are not copied: they are read from the run's events.
3. **One run per message**, `source = "chat"`, planned by `RunService.plan` when the run socket gets
   `{chat_session_id, message}`, so it streams like any studio run; answers to a Human node use
   `{chat_session_id, resume_run_id, response}`. Each message also writes a `chat_messages` row (`kind = "web"`), so
   `ChatRunService.on_settled` keeps the reply-once compare-and-set; for `web` it hands the run to
   `ChatSessionService.answer`, which writes the assistant turn instead of posting to a platform.
4. **Memory**: `{input_field: text, messages_field: [{role, content}, …]}`: the last `max_turns` exchanges (user
   messages and finished answers) plus this message. No messages field = no memory.
5. **Reply streaming**: `node_token` carries `field` (the node's output field), so the chat shows the reply field's
   tokens as the answer and the rest as steps.
6. **Retention**: the worker's maintenance loop deletes sessions idle for longer than `retention_days` once an hour.

## Consequences

- Phase 2 adds access modes, visitor tokens and an SSE stream on the same tables and service.
- A long history costs tokens; `max_turns` bounds it.
