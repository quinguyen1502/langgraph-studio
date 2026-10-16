# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0007
- Status: backlog
- Owner:
- Created: 2026-10-16
- Updated: 2026-10-16
- Requirement IDs: REQ-0004
- Design IDs:
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

- Integration branch is `main` (see DISC-0001).

## Open Questions

- Is a cron/schedule trigger also needed?

## Activity Log

- 2026-10-16: Created task during Factory import/onboarding.

## Handoff Notes

- Use branch `factory/task-0007-trigger-workflows-via-rest-api-and-webhooks` when implementation begins.
