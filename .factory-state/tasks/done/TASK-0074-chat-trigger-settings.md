# Task

## Metadata

- Project: superstep
- Task ID: TASK-0074
- Status: done (PR #98, REV-0068, QA-0068)
- Owner: Thái Quí Nguyễn
- Created: 2026-10-22
- Updated: 2026-10-22
- Requirement IDs: REQ-0044
- Design IDs: none (behaviour set in REQ-0044 and CLAR-0002)
- Architecture IDs: DEC-0009, DEC-0019, DEC-0036; new DEC-0046 (chat triggers)

## Objective

Store chat triggers per workflow and let owners manage them through the API, with the Slack scopes and webhook setup
that receiving messages needs. No message is handled yet (TASK-0075).

## Scope

### In Scope

- **Model and migration** `workflow_chat_triggers` (Alembic). Each row holds:
  - `id`, `workflow_id`, `owner` (the creator), `name`;
  - `channel_id` (the connection);
  - `place`: a Slack channel id, a Telegram chat id, or `dm` for direct messages to the bot;
  - `command`, stored lower-case;
  - `input_field` and `reply_field`;
  - `enabled` and `note` (why it stopped);
  - `last_message`, `last_run_id` and `created`.
- **`ChatTriggerService`** (DEC-0009: no FastAPI, repositories only):
  - list, create, update and delete;
  - the workflow's share right, as for schedules;
  - the connection must be one the creator may use (`ChannelService.usable`, and the org policy). Only Slack and
    Telegram are allowed;
  - `command` is one word (letters, digits, `-` and `_`, up to 32 characters). It is unique per connection and place:
    `CHAT_TRIGGER_COMMAND_TAKEN`;
  - `input_field` must be one of the workflow's input fields and `reply_field` one of its state fields (the saved
    graph), else `CHAT_TRIGGER_CONFIG_INVALID` naming the field;
  - at most 20 triggers per workflow (`CHAT_TRIGGER_LIMIT`). A missing row gives `CHAT_TRIGGER_NOT_FOUND`;
  - `stop(trigger, note)` for TASK-0075: the creator lost the share right, the connection was deleted, or the scopes
    are missing.
  - When a connection is deleted, its triggers stop with a note. When a workflow is deleted, its triggers are removed.
- **API** (JWT):
  - `GET /api/workflows/{wid}/chat-triggers`, `POST /api/workflows/{wid}/chat-triggers`,
    `PATCH /api/workflows/{wid}/chat-triggers/{tid}` and `DELETE /api/workflows/{wid}/chat-triggers/{tid}`;
  - pydantic schemas in `schemas/trigger.py`;
  - the shared envelope for errors.
- **Slack setup:**
  - `SLACK_BOT_SCOPES` adds `app_mentions:read` and `im:history`;
  - `SlackChannel.describe` reads the granted scopes (the `x-oauth-scopes` header of `auth.test`);
  - the channel `test` result and `ChannelService.public` say which chat-trigger scopes are missing;
  - the events URL `/api/channels/events/slack` is shown in the connection's public data (served in TASK-0075).
- **Telegram setup:** `register` asks for `["callback_query", "message"]`. Approvals keep working.
- **Errors:**
  - `CHAT_TRIGGER_NOT_FOUND`, `CHAT_TRIGGER_COMMAND_TAKEN`, `CHAT_TRIGGER_LIMIT`, `CHAT_TRIGGER_CONFIG_INVALID` and
    `CHAT_TRIGGER_SCOPE_MISSING`;
  - each goes in `CATALOG`, `docs/api-errors.md`, and `errors.*` in both locales.
- **DEC-0046** records:
  - the owner's answers in CLAR-0002;
  - the routing (connection + place + command);
  - who may run, and that the run belongs to the sender's studio user while using the owner's resources (DEC-0023);
  - the reply rules;
  - the Slack scopes and the shared events URL.
- **Handbook** API reference (en, vi) for the four routes.
- **Tests** `backend/tests/test_chat_triggers.py`:
  - the share right;
  - a connection the user may not use is refused;
  - a duplicate command;
  - invalid fields;
  - the limit;
  - stopping when the connection is deleted, and removal when the workflow is deleted;
  - Slack scopes read from a mocked `auth.test`;
  - Telegram `register` asks for both update kinds (`httpx.MockTransport`).

### Out Of Scope

- Receiving messages, runs and replies (TASK-0075).
- The editor dialog and the Channels page (TASK-0076).
- The handbook guide page (TASK-0077).

## Inputs

- REQ-0044, CLAR-0002.
- `backend/app/services/schedule_service.py` (share right, rows per workflow), `channel_service.py`,
  `approval_channels/slack.py`, `telegram.py`, `slack_oauth.py`, `core/config.py` (`SLACK_BOT_SCOPES`),
  `models/workflow_schedule.py`, `api/routes/triggers.py`, `schemas/trigger.py`.

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0044-chat-triggers.md`
- Clarification: `.factory-state/artifacts/CLAR-0002-chat-triggers.md`
- Design: none
- Architecture: `docs/backend-architecture.md` (DEC-0009)
- Decisions: DEC-0019 (approval channels), DEC-0023 (owner's resources), DEC-0036 (schedules), DEC-0046 (to write)
- Discovery: none

## Expected Outputs

- Model, migration, repository, `ChatTriggerService`, routes, schemas, error codes
- Slack scope check, Telegram `allowed_updates`
- DEC-0046, the handbook API reference entries
- `tests/test_chat_triggers.py`

## Implementation Notes

- Mirror `ScheduleService` for the share right, the row shape and the `note` on stopped rows.
- Read the workflow's input fields and state fields the same way the run input form and the reply field select will
  (one helper, reused by TASK-0076 through the API response).

## Constraints

- Layers (DEC-0009), with an Alembic migration that works on SQLite and Postgres. `tests/test_layers.py` passes.
- Secrets never appear in trigger responses.

## Dependencies

- None.

## Acceptance Criteria

- Owners and admins can list, create, edit and delete chat triggers. Others get the same errors as for schedules.
- A connection the creator may not use, a non-Slack/Telegram connection, a duplicate command, an unknown field and a
  21st trigger are each refused with their code.
- Deleting the connection stops its triggers with a note. Deleting the workflow removes them.
- Slack connections report missing chat-trigger scopes. Telegram webhook registration asks for messages and button
  presses.
- The new codes are in `CATALOG`, `docs/api-errors.md` and both locales (`tests/test_api_envelope.py`).
- pytest (SQLite and Postgres) and `tests/test_layers.py` pass.

## Validation Plan

- `pytest tests/test_chat_triggers.py`, the full suite, and Postgres in CI.

## Assumptions

- Slack returns the granted scopes in the `x-oauth-scopes` header of Web API responses.

## Open Questions

- None.

## Activity Log

- 2026-10-22: planned from REQ-0044 (owner accepted it and answered CLAR-0002).
- 2026-10-22: started after PR #97 merged (owner approved the plan).
- 2026-10-22: implemented; DEC-0046 written. Review REV-0068, QA QA-0068.
- 2026-10-22: CI green on PR #98 (Postgres included); the owner approved the merge.

## Handoff Notes

- None.
