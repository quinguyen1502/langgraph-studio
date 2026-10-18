# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0045
- Status: done
- Phase: hardening
- Owner: Thái Quí Nguyễn
- Created: 2026-10-18
- Updated: 2026-10-18
- Requirement IDs: REQ-0032
- Design IDs: DEC-0035
- Architecture IDs:

## Objective

Sign-in lockout, password reset links, the session in an HttpOnly cookie, and no demo account in production.

## Scope

### In Scope

- Backend: `models/auth_security.py`, `models/user.py` (`password_changed`), migration `0026_auth_hardening`, `repositories/auth_security.py`, `services/auth_service.py`, `services/mailer.py` (shared with notifications), `services/seed.py`, `api/deps.py`, `api/routes/auth.py`, the two socket routes, `core/config.py`, `core/security.py`, `core/errors.py`
- Frontend: `lib/api.ts`, `lib/password.ts`, `components/password-rules.tsx`, `components/copy-field.tsx`, `pages/Auth.tsx`, `pages/PasswordReset.tsx`, `pages/settings/UsersSection.tsx`, callers of the old token helpers, locale files
- Tests: `backend/tests/test_session_hardening.py`, `backend/tests/conftest.py`, `frontend/e2e/session.spec.ts`, `e2e/helpers.ts` (`apiToken`, `signIn`) and the specs that read the token
- Docs: both READMEs, `.env.example`, `docs/api-errors.md`

### Out Of Scope

- Self-service password change while signed in, MFA, SSO

## Inputs

- `.factory-state/artifacts/REQ-0032-auth-hardening.md`

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0032-auth-hardening.md`
- Decision: `.factory-state/decisions/DEC-0035-session-cookie-lockout-reset.md`
- Review: `.factory-state/artifacts/REV-0043-task-0045.md`
- QA: `.factory-state/artifacts/QA-0043-task-0045.md`

## Constraints

- Branch from `develop` (`4ee1ccd`). One PR into `develop`. Do not merge until the owner asks.

## Dependencies

- None. Touches `e2e/template-editor.spec.ts` (one line, the token helper) like PR #47; the conflict is trivial.

## Acceptance Criteria

- Same as REQ-0032.

## Validation Plan

- `cd backend && .venv/bin/python -m pytest -q`
- `cd frontend && npx tsc -b && npx vitest run && npx oxlint && npx vite build`
- `cd frontend && PW_CHROME=... E2E_UVICORN=../backend/.venv/bin/uvicorn npx playwright test`
- `git diff --check`

## Assumptions

- `factory ready` does not exit 0 here (the CLI needs `textual`). GitHub Actions does not run (billing). Local checks are the evidence.

## Open Questions

- None

## Activity Log

- 2026-10-18: Filed from item 5 of the remaining-work report (plus the production demo account found while answering REQ-0001); the owner asked to do it. Two findings during the work: Vite's string proxy rewrites `Host`, so the reset link is now a path the UI puts on its own origin (`url` only with `STUDIO_PUBLIC_URL`); nginx forwards `$host` without the port, so the socket origin check compares host names. The shared test clients stay on Bearer auth by making the test cookie Secure. REV-0043 has no blocking findings. QA-0043 passed. Task set to done. PR into `develop`. Not merged.

## Handoff Notes

- Signed-in users of the old UI are signed out once after deploy.
