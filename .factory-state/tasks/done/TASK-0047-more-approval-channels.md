# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0047
- Status: done
- Phase: approvals
- Owner: Thái Quí Nguyễn
- Created: 2026-10-19
- Updated: 2026-10-19
- Requirement IDs: REQ-0034
- Design IDs: DEC-0037
- Architecture IDs:

## Objective

WhatsApp, e-mail, and Microsoft Teams approval channels.

## Scope

### In Scope

- Backend: `services/approval_channels/{base,whatsapp,links,__init__}.py`, `services/approval_service.py` (`_decide`, `link_info`, `decide_link`, `challenge`, optional target), `services/channel_service.py`, `services/identity_service.py`, `api/routes/approvals.py`, `core/config.py`
- Frontend: `pages/Approve.tsx`, `App.tsx`, `lib/approvals.ts`, `components/approvals/{channel-parts,identity-row}.tsx`, `components/human-approval-settings.tsx`, locales
- Tests: `backend/tests/test_more_channels.py`, `test_approval_channels.py` (kinds now include the three), `fixtures/mock_chat_api.py` (`/teams/`), `frontend/e2e/link-approvals.spec.ts`, `playwright.config.ts` (`STUDIO_PUBLIC_URL`)
- Docs: both READMEs, `.env.example`

### Out Of Scope

- Bot Framework, inbound e-mail

## Inputs

- `.factory-state/artifacts/REQ-0034-more-approval-channels.md`

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0034-more-approval-channels.md`
- Decision: `.factory-state/decisions/DEC-0037-whatsapp-email-teams-approvals.md`
- Review: `.factory-state/artifacts/REV-0045-task-0047.md`
- QA: `.factory-state/artifacts/QA-0045-task-0047.md`

## Constraints

- Stacked on `factory/task-0046-scheduled-triggers` (PR #50), which is stacked on PR #49: e-mail uses `services/mailer.py` from #49, and the development database is already at migration `0027`. Retarget after those merge. Do not merge until the owner asks.

## Dependencies

- TASK-0045 (PR #49), TASK-0046 (PR #50).

## Acceptance Criteria

- Same as REQ-0034.

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

- 2026-10-19: Filed from item 7 of the remaining-work report; the owner asked to do it. WhatsApp as a button channel (signature, GET challenge, template mode); e-mail and Teams as link channels decided on `/approve` by the signed-in user, sharing `_decide` with the button path. Found while testing: the e-mail stub also caught the "run waiting" notification (same `mailer`), and the Teams URL holds the pinned IP, so the mock matches on `Host`. Teams webhooks must be HTTPS outside tests. REV-0045 has no blocking findings. QA-0045 passed. Task set to done. Stacked PR. Not merged.

## Handoff Notes

- Retarget the PR to `develop` after PR #49 and PR #50 merge.
