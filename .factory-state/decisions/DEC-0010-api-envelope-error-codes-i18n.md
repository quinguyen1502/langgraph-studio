# Decision Record

## Metadata

- Project: langgraph-studio
- Decision ID: DEC-0010
- Status: Accepted
- Owner: Thái Quí Nguyễn
- Created: 2026-10-16
- Updated: 2026-10-16
- Related Requirements: REQ-0001
- Related Architecture: ARCH-0001
- Related Tasks: TASK-0018

## Context

API errors were Vietnamese free text in `{"detail": ...}`. Successful responses were bare JSON. Clients could not branch on errors reliably, and the UI was Vietnamese-only.

## Decision

1. **Envelope** on every REST endpoint. Success: `{"success": true, "data": …, "error": null}`. Error: `{"success": false, "data": null, "error": {"code", "message", "details"?}}`. `meta` is reserved for pagination and is not sent yet.
2. **Error codes**: stable UPPER_SNAKE codes in one catalog (`backend/app/core/errors.py` `CATALOG`, code → HTTP status + English message template). Services raise `AppError(code, …)`. One central handler set maps AppError, 422, 404/405 and unhandled 500 to the envelope. The expired-token header `X-Auth-Error: expired` is kept.
3. **WebSocket** error events gain `error: {code, message, details?}` next to the legacy `errors` list; close code 4401 is unchanged.
4. **Frontend i18n**: react-i18next with `locales/en.json` and `locales/vi.json`. The default language comes from the browser, and the user's choice is persisted in `localStorage.lang`. Errors are translated by `errors.<CODE>`, falling back to the server's English message.
5. **Coding rules** DRY / SOLID / KISS (AGENTS.md): one envelope helper, one handler set, one catalog, one client unwrap function, every UI string in the locale files.

## Consequences

- API clients must read `data` (breaking change for direct API users; the bundled frontend is updated).
- Validator issues and node exception messages stay English (dynamic text in `details` / `errors`) and are not translated.
- `test_api_envelope.py` enforces catalog ↔ docs ↔ locale parity.

## Approval

- Approved By: Thái Quí Nguyễn (owner), 2026-10-16
