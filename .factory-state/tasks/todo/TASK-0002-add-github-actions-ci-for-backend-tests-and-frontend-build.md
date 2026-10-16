# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0002
- Status: todo
- Owner:
- Created: 2026-10-16
- Updated: 2026-10-16
- Requirement IDs: REQ-0001
- Design IDs:
- Architecture IDs: ARCH-0001

## Objective

Add a GitHub Actions workflow that runs the backend pytest suite and the frontend type-check/build on every push and pull request to `main`.

## Scope

### In Scope

- `.github/workflows/ci.yml` with backend (Python 3.13, `pip install -r backend/requirements.txt`, `pytest -q` in `backend/`) and frontend (Node 20, `npm ci`, `npm run build` in `frontend/`) jobs
- README badge/section describing CI

### Out Of Scope

- Deployment, Docker images, lint rule changes

## Inputs

- `backend/requirements.txt`, `backend/pytest.ini`, `backend/tests/`
- `frontend/package.json`, `frontend/package-lock.json`
- `project.md` Technology Discovery

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0001-mvp-baseline.md`
- Architecture: `.factory-state/artifacts/ARCH-0001-current-architecture.md`
- Discovery: `.factory-state/artifacts/DISC-0001-project-context.md`

## Expected Outputs

- `.github/workflows/ci.yml`
- Updated README and task artifact with CI run evidence

## Constraints

- No secrets required; tests run in mock mode
- Import tests need `uv` and `git` on the runner (install uv via `astral-sh/setup-uv`)

## Dependencies

- None

## Acceptance Criteria

- CI workflow triggers on push and pull_request to `main`
- Backend job runs `pytest -q` and passes (19+ tests)
- Frontend job runs `npm ci && npm run build` and passes
- A deliberately failing test makes the workflow fail (verified once, then reverted)

## Validation Plan

- Push task branch and observe a green GitHub Actions run
- Run `factory validate` and `factory verify plan`

## Assumptions

- Integration branch is `main` (see DISC-0001).

## Open Questions

- None

## Activity Log

- 2026-10-16: Created task during Factory import/onboarding.

## Handoff Notes

- Use branch `factory/task-0002-add-github-actions-ci-for-backend-tests-and-frontend-build` when implementation begins.
