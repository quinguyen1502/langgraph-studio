# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0019
- Status: done
- Owner: Grok Bot (agent)
- Created: 2026-10-17
- Updated: 2026-10-17
- Requirement IDs: REQ-0003, REQ-0004, REQ-0005, REQ-0008, REQ-0010 (follow-ups)
- Design IDs: DEC-0016
- Architecture IDs: ARCH-0001

## Objective

Resolve the open issues recorded in REV-0008 … REV-0012 (TASK-0009, 0010, 0006, 0007, 0008).

## Scope

- **HITL**: active-time duration, configurable expiry (`expired`, `RUN_EXPIRED`), pending-count badge.
- **Webhooks**: HMAC signature, per-token rate limit (`RATE_LIMITED` + Retry-After), reliable Redis queue, sync wait cap, DNS-rebinding protection.
- **Versions**: pagination, retention, no-op restore notice, conflict retry, unsaved-changes warning.
- **Infra**: migration lock (Postgres advisory / SQLite file), async Redis on the event loop.
- **Tracing**: price overrides; LangSmith duplicate prevention; document end-of-run spans.

## Acceptance Criteria

- Every item above has a test on SQLite and on Postgres + Redis (Redis-only items run with `REDIS_URL`), plus e2e where the UI changed.
- Docs: DEC-0016, REV-0008…0012 updated, README, roadmap, ARCH, backend-architecture, `.env.example`.

## Delivered

- See DEC-0016 and REV-0013.
- Migration `0007_hardening` (`workflow_tokens.signing_secret`).
- New error codes: `RUN_EXPIRED` (410) and `RATE_LIMITED` (429), in the catalog, docs and en/vi.
- Tests: `tests/test_hardening.py`, updates to `test_triggers.py` and `test_versions.py`, e2e `versions`, `hitl` and `api-trigger`.

## Links

- Review: `.factory-state/artifacts/REV-0013-task-0019.md`
- QA: `.factory-state/artifacts/QA-0013-task-0019.md`

## Activity Log

- 2026-10-17: Created and implemented on `factory/task-0019-phase-2-hardening` (stacked on TASK-0008, PR #15); moved to review.
- 2026-10-17: Status set to done to match the done/ folder. Previous Status was `review`. Review REV-0013. QA QA-0013.
