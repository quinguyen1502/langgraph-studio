# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0051
- Status: done
- Phase: engine
- Owner: Thái Quí Nguyễn
- Created: 2026-10-19
- Updated: 2026-10-19
- Requirement IDs: REQ-0037
- Design IDs: DEC-0040
- Architecture IDs: DEC-0032, DEC-0018, DEC-0009

## Objective

SMTP credentials and a Send email node.

## Scope

### In Scope

- Backend: `core/smtp.py` (new), `core/config.py` (`smtp()` shape, `STUDIO_SMTP_ALLOW_PRIVATE`, `STUDIO_EMAIL_NODE_HOURLY_LIMIT`), `core/errors.py`, `engine/emails.py` (new), `engine/providers.py` (`Smtp`, `settings_fields`, `clean_settings`), `engine/{validator,nodes,effects,ports,templating}.py`, `models/credential.py` + migration `0028_credential_settings`, `schemas/credential.py`, `api/routes/credentials.py`, `api/deps.py`, `services/{credential_service,mailer,rate_limit,run_service}.py`
- Frontend: `components/{smtp-fields,email-settings}.tsx` (new), `lib/smtp.ts` (new), `components/credentials-dialog.tsx`, `components/editor/{meta.ts,editor-config.tsx}`, `components/template-preview.tsx`, `lib/providers.ts`, `index.css` (`--node-email*`), locales
- Tests: `backend/tests/test_email_node.py` (new), `backend/tests/test_deferred.py` (wait for its own run's webhook), `frontend/e2e/send-email.spec.ts` (new), `frontend/playwright.config.ts` (local SMTP sink)
- Docs: `docs/api-errors.md`, both READMEs, `.env.example`; roadmap also marks TASK-0050 merged (PR #55)

### Out Of Scope

- Attachments, OAuth2 sign-in, inbound mail

## Inputs

- `.factory-state/artifacts/REQ-0037-send-email-node.md`

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0037-send-email-node.md`
- Decision: `.factory-state/decisions/DEC-0040-send-email-node.md`
- Review: `.factory-state/artifacts/REV-0048-task-0051.md`
- QA: `.factory-state/artifacts/QA-0048-task-0051.md`

## Constraints

- Do not merge until the owner asks.

## Dependencies

- None (branched from develop at `0dcdc9a`).

## Acceptance Criteria

- Same as REQ-0037.

## Validation Plan

- `cd backend && .venv/bin/python -m pytest -q`
- `cd frontend && npx tsc -b && npx vitest run && npx oxlint && npx vite build`
- `cd frontend && PW_CHROME=… E2E_UVICORN=../backend/.venv/bin/uvicorn npx playwright test`
- `git diff --check`

## Assumptions

- No real mailbox is used. A local `aiosmtpd` server (with sign-in) stands in for SMTP in pytest, and a sink in e2e.
- `factory ready` does not exit 0 here (the CLI needs `textual`). GitHub Actions does not run (billing). Local checks are the evidence.

## Open Questions

- None

## Activity Log

- 2026-10-19: The owner asked what e-mail features exist, then for an SMTP credential and a Send email node, and approved the proposed design with a dry run when no credential is chosen. Found while testing: aiosmtpd's `AuthResult(handled=True)` never answers a failed sign-in (the fixture now uses `handled=False`); `test_notify_webhook_signed` could pick up a late webhook from the previous test's background thread once the mailer created its TLS context earlier (the context is now created only when TLS is used, and the test waits for its own run id); i18next ate the braces of `{{state.field}}` in two hints (now passed as a value); the credentials dialog title said "LLM credentials" and is now "Credentials".
