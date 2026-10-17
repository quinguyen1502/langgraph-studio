# Decision

## Metadata

- Project: langgraph-studio
- Decision ID: DEC-0019
- Task ID: TASK-0022
- Status: proposed (draft PR)
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
- `channel_identities (user_id, kind) -> external_id`, unique per `(kind, external_id)`. A Slack/Telegram account maps to at most one studio user (`IDENTITY_TAKEN`).
- Allowed approvers are the run owner plus the e-mails listed on the Human node (`data.approval.approvers`). E-mails are resolved to user ids when the request is created; unknown e-mails are ignored.
- Refusal codes: `APPROVAL_IDENTITY_UNKNOWN` (account not linked) and `APPROVAL_FORBIDDEN`.

### Flow and resume
1. `RunService.record(status=waiting)` calls `ApprovalService.on_waiting`.
2. If the node has `data.approval.channel` and the owner connected that channel, a request is stored and posted in a background thread. If the channel is not connected, the request is audited `not_configured`, and that is all (no-op).
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

## Remaining limits
- Identity linking is self-declared and not verified. Uniqueness stops two users from claiming the same account, but someone can claim another person's account first. A verification step (bot DM with a one-time code, or Slack "Sign in with Slack") is the follow-up.
- Channel credentials are per studio user, not per organisation (no RBAC yet, TASK-0014). Approvers must exist as studio users.
- Messages and button labels are English only.
- A resume from a channel of an API-triggered run does not send that run's `callback_url` webhook again.
- Slack Enterprise Grid / multi-workspace installs (OAuth distribution) are not supported; one bot token per owner.
- No rate limit on the public callback endpoint beyond signature checks.
