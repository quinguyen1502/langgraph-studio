# Decision

## Metadata

- Project: langgraph-studio
- Decision ID: DEC-0019
- Task ID: TASK-0022
- Status: proposed (draft PR); revised by the follow-up commits on the same PR (#19), see "Follow-up" below
- Created: 2026-10-17
- Extends: DEC-0013 (human-in-the-loop), DEC-0006 (credential encryption), DEC-0014 (job queue)

## Decisions

### Adapter interface
- `services/approval_channels/base.py` `ApprovalChannel`:
  - `send_request(secrets, target, msg) -> message ref`
  - `verify(secrets, headers, body)` (raises `CHANNEL_SIGNATURE_INVALID`)
  - `handle_callback(body) -> Callback | None`
  - `acknowledge(...)`
  - `update(secrets, ref, text)`
  - plus `prepare` (validate settings), `register` (webhook set-up where the platform API allows it), and `fields` / `patterns` / `identity_pattern`.
- Adapters only speak the platform. `ApprovalService` holds the business rules: tokens, identities, authorization, audit, resume. It is the same for every channel.
- Registry: `ADAPTERS` in `approval_channels/__init__.py`. Extension point: WhatsApp (Cloud API interactive buttons, `X-Hub-Signature-256`), Teams (Adaptive Card `Action.Execute`, Bot Framework JWT) and e-mail (signed links) are one subclass each. No schema change is needed.
- **Slack:**
  - Sends with `chat.postMessage`: Block Kit section plus two buttons; the token is in each button's `value`.
  - Verifies `X-Slack-Signature` (`v0` HMAC-SHA256) with at most 5 min clock skew.
  - Refusals are answered ephemerally through `response_url`, only when it is on `hooks.slack.com` (SSRF guard).
  - Edits the original message with `chat.update`.
- **Telegram:**
  - Sends with `sendMessage` and an `inline_keyboard`; the token is in `callback_data`, which is at most 64 bytes.
  - Verifies the webhook with `X-Telegram-Bot-Api-Secret-Token` (`compare_digest`).
  - Answers with `answerCallbackQuery` (an alert when refused) and edits the message with `editMessageText`.
  - `setWebhook` is registered from the UI.

### Tokens: signed, single-use, expiring
- Format `<a|r>.<request id>.<HMAC-SHA256(key, id:decision:nonce:expires)[:16 bytes] b64url>`, 37 characters.
- The key is `crypto.derive_key("approval-token")`, derived from the studio secret key.
- The decision and the expiry are signed. Flipping approve to reject, or extending the expiry, invalidates the token.
- Single use: `approval_requests.status` is compare-and-set `pending -> approved|rejected|expired|superseded`. Exactly one caller wins, and every later press is refused with `APPROVAL_ALREADY_DECIDED`.
- Expiry: `STUDIO_APPROVAL_TTL`, default 24 h, independent of `STUDIO_WAIT_TTL`.

### Identity and authorization
- `channel_identities (user_id, kind) -> external_id`. Only a **verified** link counts (follow-up 1); a Slack/Telegram account has at most one verified studio user (`IDENTITY_TAKEN`).
- Allowed approvers are the run owner plus the e-mails listed on the Human node (`data.approval.approvers`). E-mails are resolved to user ids when the request is created; unknown e-mails are ignored.
- Refusal codes: `APPROVAL_IDENTITY_UNKNOWN` (account not linked or not verified) and `APPROVAL_FORBIDDEN`.

### Flow and resume
1. `RunService.record(status=waiting)` calls `ApprovalService.on_waiting`.
2. If the node has `data.approval.channel_id` (or the legacy `channel` kind) and that connection is usable by the owner (follow-up 2), a request is stored and posted in a background thread. If the channel is not connected, the request is audited `not_configured`, and that is all (no-op).
3. On an accepted decision a `resume` job is queued. It goes to the in-process queue, or to Redis when Redis is configured.
4. `RunWorker.resume_job` plans the resume as the owner, then claims the run `waiting -> running` (compare-and-set, with a new fencing generation) and executes with progress checkpoints.
5. The `run_resumed` event carries `by: {channel, user_id}`.
6. A recovered resume job of a run that already started continues through the normal recovery path.
- **Answered in the studio:** `plan_resume` closes the pending requests synchronously (CAS to `superseded`) and edits their messages in the background. If a channel decision is already queued, the studio refuses with `RUN_NOT_WAITING`.
- **Cancelled, expired, error or timeout run:** its open requests are closed.

### Storage
- Migration `0010_approval_channels` (idempotent; SQLite and Postgres) adds four tables:
  - `approval_channels`: one per owner and kind; `secrets` is one Fernet token of the JSON settings, and only a masked hint is returned.
  - `channel_identities`
  - `approval_requests`
  - `approval_audit`: append-only. Actions: requested, approved, rejected, denied (with code), superseded, expired, send_failed, not_configured.
- New codes are in CATALOG, docs/api-errors.md and en + vi:
  - `CHANNEL_KIND_UNSUPPORTED`, `CHANNEL_CONFIG_INVALID`, `CHANNEL_NOT_FOUND`, `CHANNEL_PUBLIC_URL_REQUIRED`, `CHANNEL_SIGNATURE_INVALID`, `CHANNEL_API_FAILED`
  - `IDENTITY_INVALID`, `IDENTITY_TAKEN`
  - `APPROVAL_TOKEN_INVALID`, `APPROVAL_TOKEN_EXPIRED`, `APPROVAL_ALREADY_DECIDED`, `APPROVAL_IDENTITY_UNKNOWN`, `APPROVAL_FORBIDDEN`
- The callback endpoint returns 200 for refusals (`{outcome: "refused", code}`) so the platform does not retry. Only an unauthenticated request gets 401.

## Follow-up (resolving the first version's limits)

Done as follow-up commits on the same draft PR (#19), not as a stacked TASK-0023 PR, because they revise the design
of a PR that has not been merged yet. One commit per item; migrations `0011`–`0015`, all idempotent, SQLite (batch) and Postgres.

1. **Verified identities** (`0011_identity_verification`, `services/identity_service.py`).
   - Linking stores the account unverified. `POST /api/approvals/identities/{kind}/send-code` makes the bot DM a 6-digit code, and `POST .../verify {code}` confirms it.
   - The code is stored only as `HMAC(derive_key("identity-code"), uid:kind:external:code)`.
   - Limits: it expires after `STUDIO_IDENTITY_CODE_TTL` (600 s); `STUDIO_IDENTITY_CODE_ATTEMPTS` (5) wrong codes are allowed, counted atomically; it can be resent every `STUDIO_IDENTITY_CODE_RESEND` (30 s), otherwise `RATE_LIMITED`.
   - The `(kind, external_id)` unique constraint is dropped, so an unverified claim cannot squat on somebody else's account. Uniqueness among verified links is checked at verify time.
   - Links from the first version stay unverified on purpose.
   - New codes: `IDENTITY_NOT_LINKED`, `IDENTITY_CODE_INVALID {left}`, `IDENTITY_CODE_EXPIRED`, `IDENTITY_CODE_ATTEMPTS`.
   - Adapter: `send_dm`. Slack uses `chat.postMessage` to the user id, scope `im:write`. Telegram uses `sendMessage` to the user id; the user must have pressed Start.
2. **Org-wide channels** (`0012_org_channels`, `services/channel_service.py`).
   - `users.is_admin` is set from `STUDIO_ADMIN_EMAILS` at sign-up and start-up; the demo user is an admin outside production.
   - `approval_channels.scope` is `user` or `org`. An org connection is created, edited and deleted only by admins (`CHANNEL_ADMIN_REQUIRED`), and every user can use it. Personal connections stay.
   - REST by id: `POST /channels`, `PUT|DELETE /channels/{id}`, `POST /channels/{id}/register-webhook`.
   - The Human node stores `{channel_id, channel, target, approvers}`. A legacy `{channel}` resolves to the owner's personal connection, else to the org one. Another user's personal connection is never usable.
   - The verification DM goes through the personal connection, else the org one.
   - `ChannelService` (connections, visibility, lookups) was split out of `ApprovalService` (requests, decisions, audit).
3. **en/vi chat texts** (`0014_user_lang`, `approval_channels/messages.py`).
   - Requests, buttons and the edited message use the run owner's language. Private answers (refusals, acknowledgements) use the presser's. Codes use the user's own.
   - `users.lang` is saved through the notification preferences (`lang: en|vi`). The studio's language switcher writes it, and it is synced once per session after sign-in.
4. **API callback after a channel resume** (`0015_run_callbacks`).
   - An API run stores `callback_url` and `callback_token_id`. `RunWorker._deliver` queues the webhook through `DeliveryService` (signed, retried, listed) for start jobs and for channel resume jobs.
   - The fenced `RunRepository.add` writes only the attributes that are set, so the stored callback survives checkpoints.
5. **Several Slack workspaces (and Telegram bots) per owner** (`0013_channel_accounts`).
   - Saving a connection calls `describe` (Slack `auth.test`, Telegram `getMe`), which validates the credentials and stores `team_id` plus a name.
   - There is one connection per owner, scope and account: the same workspace replaces the existing one, another workspace adds a new one.
   - Shared Slack Request URL `POST /api/approvals/callback/slack`: it routes by the payload's `team.id` and verifies the signature against those connections' signing secrets. An unknown team gets the same 401. When the same app is connected twice, the request's own connection is chosen. The per-connection URL still works.
6. **Callback rate limits.**
   - Uses the TASK-0019 `RateLimiter` (shared via Redis) before any decryption or signature work.
   - Limits: per client IP (`STUDIO_CALLBACK_RATE_LIMIT_IP`, 60) and per connection or claimed Slack team (`STUDIO_CALLBACK_RATE_LIMIT_CHANNEL`, 300) per `STUDIO_CALLBACK_RATE_WINDOW` (60 s). Over the limit: `429 RATE_LIMITED` with `Retry-After`.
   - `STUDIO_TRUST_PROXY=1` takes the last `X-Forwarded-For` hop, which our nginx appends. Compose sets it.

## Remaining limits
- An approver needs a usable connection (their own, or an org one) of that platform to receive a verification code. Telegram also needs the user to have started the bot.
- Slack user ids are assumed unique across workspaces (true for normal workspaces; Enterprise Grid shares ids, which is fine). Identities are stored per platform, not per workspace.
- Two users verifying the same account at the same moment: the check-then-set is not one transaction, so in a tiny window both could be verified. A button press would then map to either of them. A partial unique index on verified links would close this; it is not portable to every SQLite version we support, so it is left out.
- A waiting API run answered in the studio UI (WebSocket resume), rather than from a channel, still does not re-send `callback_url` (the WebSocket path has no delivery hook).
- `STUDIO_TRUST_PROXY` trusts exactly one proxy hop.
- Slack Enterprise Grid org-wide installs and OAuth distribution are not supported: each workspace is a bot token pasted by a user or an admin.
- Admins are managed by environment variable only (no admin UI or RBAC yet, TASK-0014).
