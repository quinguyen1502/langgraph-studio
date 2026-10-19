# Decision Record

## Metadata

- Project: langgraph-studio
- Decision ID: DEC-0040
- Status: Accepted
- Owner: Thái Quí Nguyễn
- Created: 2026-10-19
- Updated: 2026-10-19
- Related Requirements: REQ-0037
- Related Architecture: DEC-0032 (provider registry), DEC-0018 (effectively-once), DEC-0009 (layers), DEC-0034 (templating)
- Related Tasks: TASK-0051

## Context

System e-mail goes through `services/mailer.py` and the admin's `SMTP_HOST`. Credentials are per-user provider records (encrypted secret, base URL, extra headers). The engine may import `core` but not `services`.

## Decision

1. **SMTP is a provider.** `Smtp` in `engine/providers.py` has `kind = "email"` and `settings_fields`. Credentials get a non-secret JSON `settings` column (migration `0028`): host, port, security (`starttls` | `ssl` | `none`), username, from_email, from_name. The password is the existing encrypted secret. Test connection (`list_models`) connects, upgrades to TLS, signs in and quits.
2. **One SMTP implementation in `core/smtp.py`**, used by Send email nodes and by `services/mailer.py` (system e-mail now goes through it too).
   - The host is resolved once, private addresses are refused unless allowed, and the socket connects to that IP while TLS verifies the host name (same idea as `core/net.py` for HTTP).
   - STARTTLS is required for credentials (a password is never sent in clear when the server does not offer it); system e-mail keeps the old opportunistic behaviour.
   - Sign-in uses one mechanism (PLAIN, else LOGIN, else CRAM-MD5): after a refusal, smtplib's `login()` tries the next one, which some servers answer by hanging.
3. **A node type `email`** (`engine/emails.py`). Addresses come from templates (one reference may hold a list). Subject newlines are folded so no header can be injected. In HTML, inserted values are escaped (`render(..., escape=html.escape)`) and a plain text part is derived. Bcc never appears in the headers.
4. **No credential = dry run.** Nothing is sent; the result shows recipients, subject and a text preview. The studio's own SMTP is never used for workflow mail.
5. **Effectively-once.** `email` is in `SIDE_EFFECT_TYPES`; the ledger returns the recorded result on recovery, and the Message-ID is `<idempotency-key@sender-domain>` so a receiver can drop a duplicate. It is not a runtime-policy type: the editor offers no retry or cache settings, and the validator refuses `retry` and `cache_ttl` sent through the API, because a retry after the server accepted DATA would send twice and a cache hit would skip a send.
6. **Quota.** `Ports.email_quota` is bound per resource owner by `RunService`. It counts recipients in a fixed one-hour window with `rate_limit.Counter` (Redis when `REDIS_URL` is set, else in-process), the blocking twin of the request rate limiter.

## Rationale

- Reusing the provider registry gives encryption, ownership, transfer rebinding, template stripping, the credential dialog and the delete confirmation for free.
- One SMTP module keeps TLS, SSRF and error handling in one place.

## Alternatives Considered

- Option: A separate "Email accounts" resource
  - Tradeoffs: A second table, API and dialog with the same ownership rules
  - Reason Not Chosen: Credentials already do this
- Option: Store host and user in `base_url` (`smtp://user@host:587`)
  - Tradeoffs: Mixes a URL check meant for HTTP with SMTP; the sender still needs a place
  - Reason Not Chosen: An explicit `settings` column is clearer
- Option: Fall back to the studio's `SMTP_HOST`
  - Tradeoffs: Any author could send as the studio's address
  - Reason Not Chosen: The owner chose the dry run

## Consequences

- `/api/providers` lists `settings_fields`; credential create, update and test accept `settings`.
- `config.smtp()` now returns core/smtp settings (`username`, `security`, ...). Only the mailer reads them.
- New codes: `CREDENTIAL_SETTINGS_INVALID`, `EMAIL_*` (docs/api-errors.md).
