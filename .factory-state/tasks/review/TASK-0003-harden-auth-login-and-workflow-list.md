# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0003
- Status: todo
- Owner: Grok Bot (agent)
- Priority: Phase 1 Feasibility, step 3 — after TASK-0002 (CI), before TASK-0004 (core hardening)
- Created: 2026-10-16
- Updated: 2026-10-16
- Requirement IDs: REQ-0001
- Design IDs:
- Architecture IDs: ARCH-0001

## Objective

Prove the login → workflow list → open → run path is solid: harden registration/login rules, token expiry handling, error/empty/loading states on the auth and list screens, list edge cases, and add browser end-to-end tests for the full path.

## Scope

### In Scope

- Password rules on register (min length 8, at least one letter and one digit; clear messages); email normalisation; generic login error (no user enumeration)
- ~~Basic login throttling~~ — **Deferred** (owner decision 2026-10-16): no lockout / rate limiting in this task
- Token expiry: frontend detects 401/expired JWT, redirects to `/login?expired=1` with a notice and returns to the original page after login; `JWT_SECRET` required outside dev (warning at startup when the placeholder is used)
- Auth screens: loading, error, disabled-submit states; keyboard/enter submit; accessible labels
- Workflow list edge cases: empty list, search with no results, long names, many workflows (≥100) render and search fast, rename to empty/duplicate name handled, delete of the currently open workflow, deleted/foreign workflow URL shows a not-found state
- Editor open/run: friendly not-found and error states; run panel shows auth expiry during a run
- E2E tests (Playwright, headless Chromium) for: register → login → list → open example → run → done; wrong password; expired token redirect; rename/duplicate/delete with confirm
- `npm run` script / pytest marker for E2E so CI can run it (CI job may be added later if runtime too long)

### Out Of Scope

- SSO, password reset by email, RBAC (TASK-0014)
- Login rate limiting / account lockout (deferred by owner 2026-10-16; candidate for a later hardening task)
- Core compiler/runtime hardening (TASK-0004)

## Inputs

- `.factory-state/artifacts/REQ-0001-mvp-baseline.md`
- `.factory-state/artifacts/ARCH-0001-current-architecture.md`
- `backend/app/auth.py`, `backend/app/main.py` (auth + workflow endpoints)
- `frontend/src/pages/Auth.tsx`, `frontend/src/pages/Workflows.tsx`, `frontend/src/pages/Editor.tsx`, `frontend/src/lib/api.ts`

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0001-mvp-baseline.md`
- Architecture: `.factory-state/artifacts/ARCH-0001-current-architecture.md`
- Discovery: `.factory-state/artifacts/DISC-0001-project-context.md`
- Decision: `.factory-state/decisions/DEC-0007-phased-replan-and-task-renumbering.md`
- Related tasks: TASK-0002 (CI), TASK-0004 (core hardening)

## Expected Outputs

- Backend and frontend changes for the rules and states above
- New pytest cases (password rules, expiry, names) and Playwright E2E suite
- README section for running E2E tests; REV and QA artifacts

## Constraints

- Keep the demo user `admin@example.com / admin123` working in dev (seeded user exempt from new password rules, documented)
- No new external services

## Dependencies

- TASK-0002 (pyproject/CI) merged or stacked on its branch (document which)

## Acceptance Criteria

- Register rejects weak passwords with a specific message; login errors are generic (throttling deferred — see Scope)
- An expired or invalid token on any page redirects to `/login` with an "expired" notice and returns to the original URL after login
- Startup logs a warning when `JWT_SECRET` is the placeholder
- List shows distinct empty and no-search-result states; 100+ workflows render and filter without visible lag; empty rename is rejected
- Opening a deleted or foreign workflow shows a not-found state with a link back to the list
- Playwright E2E suite passes headless: register→login→list→open→run→done, wrong password, expired token, rename/duplicate/delete
- Existing backend tests and `npm run build`/`lint` still pass

## Validation Plan

- `cd backend && .venv/bin/python -m pytest -q`
- `cd frontend && npm run build && npm run lint`
- E2E: start `./dev.sh`, run the Playwright suite headless
- `factory verify run --profile full`, `factory validate`
- GitHub Actions green on the PR (once account billing is resolved)

## Assumptions

- Throttling can be in-memory for the MVP (resets on restart)

## Open Questions

- Password policy acceptable as proposed (≥8, letter+digit)? Implemented as proposed; owner confirms in PR review.
- Should E2E run in CI on every PR or nightly? Not added to CI yet (Actions blocked by billing); suite runs locally in ~20 s.

## Activity Log

- 2026-10-16: Created task during owner re-plan (DEC-0007). Not started.
- 2026-10-16: Moved todo -> doing on `factory/task-0003-harden-auth-login-and-workflow-list` (from PR #4 branch + merged TASK-0002 branch).
- 2026-10-16: Owner decision: login rate limiting / lockout out of scope (deferred). A prototype was removed before commit.
- 2026-10-16: Implemented backend rules, frontend states, Playwright E2E (5 tests), screenshots. Local: pytest 32 passed, build + lint OK, E2E 5 passed, `factory verify run --profile full` passed.
- 2026-10-16: Moved doing -> review. Review: REV-0003-task-0003; QA: QA-0003-task-0003.

## Handoff Notes

- Branch `factory/task-0003-harden-auth-login-and-workflow-list`; PR base `factory/replan-renumber-tasks` (PR #4). The branch also merges the TASK-0002 branch (PR #1) for pyproject/conftest/CI. Merge after #4 and #1, then retarget to `main`.
- Deferred: login throttling / lockout.
- E2E: `cd frontend && npm run e2e` (needs `backend/.venv`; `PW_CHROME` to use system Chrome). Not in CI yet.
- Review: `.factory-state/artifacts/REV-0003-task-0003.md`; QA: `.factory-state/artifacts/QA-0003-task-0003.md`.
