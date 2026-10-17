# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0005
- Previous ID: TASK-0003 (renumbered 2026-10-16, DEC-0007)
- Status: review
- Owner:
- Created: 2026-10-16
- Updated: 2026-10-16
- Requirement IDs: REQ-0002
- Design IDs:
- Decision IDs: DEC-0006
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

- Stacked on TASK-0002 branch (`factory/task-0002-add-github-actions-ci-for-backend-tests-and-frontend-build`, PR #1): uses its pyproject.toml, conftest.py and CI. PR base is that branch.

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

- 2026-10-16: Owner approved porting onto the layered backend (TASK-0017, PR #8). Recreated on `factory/task-0005-llm-providers-credentials-layered` (based on `factory/task-0017-restructure-backend-layers`); the old branch was not force-pushed. Mapping: `core/crypto.py`, `models/credential.py` + Alembic `0002_credentials`, `repositories/credentials.py`, `services/credential_service.py` (user-bound resolver handed to `run_stream(resolve=...)` via `RunPlan`), `api/routes/credentials.py`, `engine/llm.py` (providers). Kept PR #2 tests (`test_llm_providers.py`, password updated to the TASK-0003 rules) and added credential service tests with fake repos, a migration adoption test, and E2E `credentials.spec.ts`. Results: pytest 81 passed; build OK; E2E 11 passed. REV-0002/QA-0002 addendum.

- 2026-10-16: Renumbered TASK-0003 -> TASK-0005 (Phase 1 step 5) per DEC-0007. Branch name keeps the old ID.
- 2026-10-16: Moved todo -> doing on `factory/task-0003-configure-real-llm-providers-with-per-workflow-credentials` (stacked on TASK-0002).
- 2026-10-16: Implemented `backend/app/credentials.py` (Fernet at rest, masked hints), credential CRUD API, provider calls for OpenAI/compatible + Anthropic via injectable httpx client, per-node `credential_id`, Credentials dialog + LLM node credential select. Tests: `backend/tests/test_llm_providers.py` (7 tests, mocked HTTP). Local: pytest 26 passed; factory verify run --profile full PASSED. Moved to review.

- 2026-10-16: Created task during Factory import/onboarding.

## Handoff Notes

- Review: `.factory-state/artifacts/REV-0002-task-0005.md`; QA: `.factory-state/artifacts/QA-0002-task-0005.md`; decision: `.factory-state/decisions/DEC-0006-llm-credential-model.md`
- No real API keys were used; real-provider smoke test is left for the owner.
- GitHub Actions blocked by account billing (same as TASK-0002).

- Active branch: `factory/task-0005-llm-providers-credentials-layered` (new draft PR, replaces #2). Old branch kept unchanged for reference.
