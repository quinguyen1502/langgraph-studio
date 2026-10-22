# Decision Record

## Metadata

- Project: superstep
- Decision ID: DEC-0046
- Status: Accepted
- Owner: Thái Quí Nguyễn
- Created: 2026-10-22
- Updated: 2026-10-22
- Related Requirements: REQ-0044 (owner answers in CLAR-0002)
- Related Architecture: DEC-0009 (layers), DEC-0019 (approval channels), DEC-0023 (sharing, the owner's resources),
  DEC-0036 (schedules)
- Related Tasks: TASK-0074, TASK-0075, TASK-0076, TASK-0077

## Context

REQ-0044 starts a workflow from a message to the Slack app or Telegram bot that approvals already use. The owner
answered CLAR-0002 with the recommended options:

- **Who may run:** only verified linked chat accounts whose studio user may run the workflow.
- **Routing:** a command word picks the workflow.
- **Reply:** the bot shows one chosen state field.
- **Input:** the message text goes into one chosen input field.

## Decision

1. **A trigger is a row per workflow** (`workflow_chat_triggers`). It holds:
   - the connection (`channel_id`, an approval connection of DEC-0019);
   - the place: a Slack channel id (`C…` / `G…`), a Telegram chat id (groups are negative), or `dm` for direct
     messages to the bot;
   - a lower-case command word: letters, digits, `-` and `_`, up to 32 characters. A leading `/` is dropped, so
     `/leave` and `leave` are the same command;
   - the input field and the reply field, both names in the saved graph's state;
   - on/off, and a note on why it stopped;
   - the last message time and last run.
2. **One trigger per message.** The command is unique per connection and place (a unique index on
   `channel_id, place, command`, checked first in the service: `CHAT_TRIGGER_COMMAND_TAKEN`). The same command may
   be used in another place or on another connection.
3. **Managing triggers needs the share right** (owner or admin), as for schedules and API tokens. The creator must be
   able to use the connection: their own personal one, or an org one when the org policy lets their role use org
   connections. Only connections whose adapter sets `chat` (Slack, Telegram) qualify. There are at most 20 triggers
   per workflow (`CHAT_TRIGGER_LIMIT`).
4. **Stopping, not deleting.**
   - Deleting a connection turns its triggers off with the note `channel`. Turning one back on fails until it names
     a connection the user may use.
   - Deleting the workflow deletes its triggers.
   - TASK-0075 turns a trigger off with `access` when its creator has lost the share right, as the scheduler does.
5. **Slack scopes.**
   - Chat triggers need `app_mentions:read` (mentions in channels) and `im:history` (direct messages to the bot).
     `SLACK_BOT_SCOPES` ("Add to Slack") asks for them.
   - `SlackChannel.describe` reads the granted scopes from the `x-oauth-scopes` header of `auth.test`. Connections
     store them (`approval_channels.scopes`) when they are saved or tested.
   - A trigger cannot be turned on while the scopes are known to be missing (`CHAT_TRIGGER_SCOPE_MISSING`). It can be
     saved off.
   - Unknown scopes (an older connection, not tested since) do not block. The Channels page asks the user to test
     the connection.
6. **Where messages arrive.**
   - Slack has one Event Subscriptions URL for every workspace, `/api/channels/events/slack`, routed by `team_id`.
     The connection's public data shows it (`chat.events_url`).
   - Telegram allows one webhook per bot, so messages arrive at the existing callback URL. "Register webhook" now
     asks for `["callback_query", "message"]`.
7. **Runs** (TASK-0075).
   - A run is owned by the sender's linked studio user, who must have the run right.
   - It uses the workflow owner's credentials and resources, like every run of a saved workflow (DEC-0023).
   - `source="chat"`.
   - The input is `{input_field: text}`. When the input field is a list, the text is wrapped in a one-item list.
8. **Replies** (TASK-0075).
   - The reply shows only the status, the chosen field (shortened to the platform's limit), the waiting node's label
     and the run link.
   - Refusals go to the sender only.

## Consequences

- Slack workspaces installed before TASK-0074 must reinstall the app (or add the two scopes and the event
  subscription by hand) before their triggers can be turned on. Telegram bots must press "Register webhook" again
  to receive messages.
- `ChannelService.public` carries a `chat` block (`missing_scopes`, `events_path`, `events_url`). It is `null` for
  connections that cannot start runs.
- TASK-0075 records here where it stores the chat reference of a run (new run columns or a small table).
