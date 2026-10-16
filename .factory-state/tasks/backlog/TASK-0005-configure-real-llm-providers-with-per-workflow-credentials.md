# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0005
- Previous ID: TASK-0003 (renumbered 2026-10-16, DEC-0007)
- Status: backlog
- Owner:
- Created: 2026-10-16
- Updated: 2026-10-16
- Requirement IDs: REQ-0002
- Design IDs:
- Architecture IDs: ARCH-0001

## Objective

Implement REQ-0002: Configure real LLM providers with per-workflow credentials.

## Scope

### In Scope

- Deliver the in-scope items of `.factory-state/artifacts/REQ-0002-real-llm-providers.md`

### Out Of Scope

- Out-of-scope items listed in REQ-0002

## Inputs

- `.factory-state/artifacts/REQ-0002-real-llm-providers.md`
- `.factory-state/artifacts/ARCH-0001-current-architecture.md`

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0002-real-llm-providers.md`
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

- An LLM node configured with a stored OpenAI or Anthropic credential returns the provider response during a run
- Credentials are never returned by any API response or written to logs
- Without credentials the existing mock behaviour and tests are unchanged
- Provider errors surface as a node `error` event, not a server crash

## Validation Plan

- `cd backend && .venv/bin/python -m pytest -q`
- `cd frontend && npm run build`
- Manual run of the seeded example

## Assumptions

- Integration branch is `main` (see DISC-0001).

## Open Questions

- Credential scope: per user, per workflow, or global admin?
- Which providers are required first?

## Activity Log

- 2026-10-16: Renumbered TASK-0003 -> TASK-0005 per owner re-plan (DEC-0007).
- 2026-10-16: Created task during Factory import/onboarding.

## Handoff Notes

- Use branch `factory/task-0005-configure-real-llm-providers-with-per-workflow-credentials` when implementation begins.
