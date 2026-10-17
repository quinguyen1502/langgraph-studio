# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0007
- Status: review
- Owner: Grok Bot (agent)
- Created: 2026-10-16
- Updated: 2026-10-16
- Requirement IDs: REQ-0004
- Design IDs: DEC-0014
- Architecture IDs: ARCH-0001

## Objective

Implement REQ-0004: Trigger workflows via REST API and webhooks.

## Scope

### In Scope

- Deliver the in-scope items of `.factory-state/artifacts/REQ-0004-api-webhook-trigger.md`

### Out Of Scope

- Out-of-scope items listed in REQ-0004

## Inputs

- `.factory-state/artifacts/REQ-0004-api-webhook-trigger.md`
- `.factory-state/artifacts/ARCH-0001-current-architecture.md`

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0004-api-webhook-trigger.md`
- Architecture: `.factory-state/artifacts/ARCH-0001-current-architecture.md`
- Discovery: `.factory-state/artifacts/DISC-0001-project-context.md`

## Expected Outputs

- Implementation, tests, README update
- Design/architecture artifact if the requirement changes boundaries

## Constraints

- Mock mode and existing tests must keep passing

## Dependencies

- TASK-0002 (CI) recommended first

## Acceptance Criteria

- A POST with a valid workflow token starts a run and returns run id and (sync mode) final state
- Invalid or revoked tokens return 401
- Runs started via API appear in run history with source `api`

## Validation Plan

- `cd backend && .venv/bin/python -m pytest -q`
- `cd frontend && npm run build`
- Manual run of the seeded example

## Assumptions

- Phase 2 integrates into `develop`; stacked on TASK-0006 (PR #13).

## Open Questions

- Is a cron/schedule trigger also needed? **Resolved (DEC-0014): not in this task (out of scope in REQ-0004); a scheduler can call the same endpoint later.**

## Delivered

- `workflow_tokens` + `runs.source` (migration `0005_api_triggers`); token create/list/revoke (owner); `POST /api/hooks/workflows/{wid}/runs` (async 202 / sync) and `GET …/runs/{run_id}` with the workflow token.
- `JobQueue` (memory / Redis list) + `RunWorker` (in-process via lifespan, or `python -m app.worker`); compose `worker` service; cancel of queued runs.
- Result webhook with SSRF guard; error codes `TRIGGER_TOKEN_INVALID`, `TOKEN_NOT_FOUND`, `CALLBACK_URL_INVALID` (catalog, docs, en/vi).
- UI: "API" dialog (tokens, copy-once, curl example), API badge in history.
- Tests: `tests/test_triggers.py`, `e2e/api-trigger.spec.ts`; compose smoke covers a sync trigger through the worker. Docs: DEC-0014, ARCH-0001, backend-architecture, README, roadmap, REV-0011, QA-0011.

## Activity Log

- 2026-10-16: Implemented on `factory/task-0007-trigger-workflows-via-rest-api-and-webhooks` (stacked on TASK-0006); moved to review.

- 2026-10-16: Created task during Factory import/onboarding.

## Handoff Notes

- Use branch `factory/task-0007-trigger-workflows-via-rest-api-and-webhooks` when implementation begins.
