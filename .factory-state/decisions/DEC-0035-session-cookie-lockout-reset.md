# Decision Record

## Metadata

- Project: langgraph-studio
- Decision ID: DEC-0035
- Status: Accepted
- Owner: Thái Quí Nguyễn
- Created: 2026-10-18
- Updated: 2026-10-18
- Related Requirements: REQ-0032, REQ-0001
- Related Architecture:
- Related Tasks: TASK-0045

## Context

The browser kept the JWT in `localStorage`, where any script on the page could read it. There was no sign-in lockout and no password reset. The demo account `admin@example.com` / `admin123` was created in production too. The owner asked to fix these (remaining-work item 5).

## Decision

1. **Session cookie.** Login and registration set `studio_session`: HttpOnly, `SameSite=Lax`, `Path=/`, with `Max-Age` matching the JWT lifetime, and `Secure` when `STUDIO_COOKIE_SECURE` is on (the default in production). The body still returns `token` and `expires_at`, so API clients keep working. The page stores only `user` and `session_exp`.
2. **CSRF.** A Bearer header takes precedence. A request authenticated by the cookie with POST, PUT, PATCH, or DELETE must send `X-Requested-With: studio`; otherwise it gets `AUTH_CSRF`. This header forces a CORS preflight, and SameSite=Lax already keeps the cookie off cross-site writes. A socket authenticated by the cookie must come from the server's host (ports ignored) or an allowed CORS origin.
3. **Lockout.** `login_throttle` counts failures per normalised e-mail, including unknown ones. Five within 15 minutes lock that e-mail for 15 minutes (`AUTH_LOCKED`), and a lock refuses even the right password. A successful sign-in or a password reset clears the count.
4. **Reset links.** `password_resets` stores the SHA-256 of a random 32-byte token, with an expiry (1 h), the time it was used, and who made it. An admin makes a link in Settings → Users. With SMTP and `STUDIO_PUBLIC_URL` set, "forgot password" e-mails one and answers the same way for every address. Using a link sets `users.password_changed`, and any token with an `iat` earlier than that second stops working. Both the link and its use are recorded in the audit log.
5. **Demo account.** It is seeded only outside production. In production, an existing demo account that still verifies with `admin123` is deactivated at start-up, and `STUDIO_ADMIN_EMAILS` bootstraps an admin.

## Rationale

- An HttpOnly cookie removes token theft by XSS. A header-based CSRF check is stateless and fits the single `api()` client.
- Counting per e-mail stops password guessing against one account without IP tracking, which behind proxies needs `STUDIO_TRUSTED_PROXIES`.
- Admin-made links work on any deployment; e-mail is an extra where SMTP exists.

## Alternatives Considered

- Option: Keep `localStorage` and add a Content Security Policy
  - Benefits: No auth change
  - Tradeoffs: A policy narrows XSS but any script that does run can still read the token
  - Reason Not Chosen: Moving the token out of script reach is the actual fix
- Option: Double-submit CSRF token
  - Benefits: Works for cross-origin UIs too
  - Tradeoffs: A second cookie and a token to rotate
  - Reason Not Chosen: The UI is same-origin; a custom header is enough
- Option: Lock by IP address
  - Benefits: Also slows spraying many accounts
  - Tradeoffs: Shared NAT and proxies lock out innocent users; needs trusted proxy configuration
  - Reason Not Chosen: Per e-mail matches the risk (one account's password); the existing rate limiter covers request floods

## Impacts

- e2e specs read a Bearer token with `apiToken()` (a login call) instead of `localStorage`.
- Pytest sets `STUDIO_COOKIE_SECURE=1`, so the shared `http://testserver` clients test Bearer auth as before.
- Users of an older UI are signed out once (their `localStorage` token is removed).

## Risks

- A lock can be triggered on purpose for a known e-mail (15 minutes). An admin reset link clears it.
- A deployment served over plain HTTP with `STUDIO_ENV=production` must set `STUDIO_COOKIE_SECURE=0`, or the browser never sends the cookie.

## Follow-Up

- None
