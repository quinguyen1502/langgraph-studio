# Requirement

## Metadata

- Project: langgraph-studio
- Requirement ID: REQ-0004
- Status: Proposed
- Owner: Thái Quí Nguyễn
- Created: 2026-10-16
- Updated: 2026-10-16
- Source: project-specs.md (Post-MVP Scope)

## Summary

Trigger workflows via REST API and webhooks. External systems can start a workflow run with JSON input and receive results synchronously or via callback.

## Problem Or Opportunity

External systems can start a workflow run with JSON input and receive results synchronously or via callback.

## Scope

### In Scope

- Per-workflow API tokens
- POST run endpoint (sync + async)
- Optional result webhook

### Out Of Scope

- Scheduled/cron triggers

## Stakeholders Or Users

- Internal developers and learners using LangGraph Studio
- Project owner (administrator)

## Current Context

- Runs are only started from the browser WebSocket

## Desired Behavior

External systems can start a workflow run with JSON input and receive results synchronously or via callback.

## Business Rules

- None

## Constraints

- Mock/offline mode must keep working without API keys.
- Must not break existing auth/ownership rules.

## Acceptance Criteria

- A POST with a valid workflow token starts a run and returns run id and (sync mode) final state
- Invalid or revoked tokens return 401
- Runs started via API appear in run history with source `api`

## Edge Cases

- Missing credentials or unavailable external services produce clear `error` events.

## Assumptions

- Stack direction in `project-specs.md` (Preferred) remains in place.

## Open Questions

- Is a cron/schedule trigger also needed?

## Related Artifacts

- `project-specs.md`
- `.factory-state/artifacts/ARCH-0001-current-architecture.md`
- `.factory-state/artifacts/DISC-0001-project-context.md`
