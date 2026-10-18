# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0002
- Status: done
- Owner:
- Created: 2026-10-16
- Updated: 2026-10-16
- Requirement IDs: REQ-0001
- Design IDs:
- Decision IDs: DEC-0001, DEC-0002, DEC-0003, DEC-0004, DEC-0005
- Architecture IDs: ARCH-0001

## Objective

Add GitHub Actions CI (backend pytest on Python 3.12; frontend `npm ci && npm run build` on Node 20 and 22, with caching) for pushes and PRs to `main`, and unblock Factory deps/verify (DEC-0005): import workspaces outside the repo by default and a backend `pyproject.toml`.

## Scope

### In Scope

- Move default import workspace to `~/.langgraph-studio/imports` (`STUDIO_IMPORT_DIR` override; earlier imports keep working)
- Add `backend/pyproject.toml` (deps, `dev` extra, pytest config); keep `requirements.txt`
- Approve GitHub Actions in intake and publish `factory stack` output (`factory-verify.yml`)
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
- Backend job (Python 3.12, pip + uv cache) runs `pytest -q` and passes
- Frontend jobs (Node 20 and 22, npm cache) run `npm ci && npm run build` and pass
- Import workspaces default outside the repository; `STUDIO_IMPORT_DIR` overrides; README documents it; previously imported workflows still run
- `backend/pyproject.toml` exists; `factory deps plan` and `factory verify plan` list only `backend` and `frontend` targets
- `factory deps apply`, `factory verify run --profile full` and `factory validate` pass

## Validation Plan

- GitHub Actions run on the PR is green (ci.yml + factory-verify.yml)
- Local: `factory deps apply --allow-network`, `factory verify run --profile full`, `factory validate`, `factory ready`
- Run an existing imported workflow after migration

## Assumptions

- Integration branch is `main` (see DISC-0001).

## Open Questions

- None

## Activity Log

- 2026-10-16: pytest moved to base deps after clean-clone factory-verify simulation failed (no pytest). Opened Draft PR #1; CI blocked by billing. Moved to review.

- 2026-10-16: Created task during Factory import/onboarding.
- 2026-10-16: Scope extended per DEC-0005; moved to doing on branch `factory/task-0002-add-github-actions-ci-for-backend-tests-and-frontend-build`.
- 2026-10-16: Implemented ci.yml, backend/pyproject.toml, tests/conftest.py, import dir default; migrated local imports to ~/.langgraph-studio/imports. Local: pytest 19 passed; factory deps apply OK; factory verify run --profile full PASSED (backend test, frontend build, frontend lint).

- 2026-10-17: Status set to done to match the done/ folder. Previous Status was `review`. Review REV-0001. QA QA-0001.

## Handoff Notes

- Draft PR: https://github.com/quinguyen1502/langgraph-studio/pull/1
- Review: `.factory-state/artifacts/REV-0001-task-0002.md`; QA: `.factory-state/artifacts/QA-0001-task-0002.md`
- Blocker: GitHub Actions jobs not started due to account billing/spending limit; owner must fix billing and re-run checks before QA can pass.

- Use branch `factory/task-0002-add-github-actions-ci-for-backend-tests-and-frontend-build` when implementation begins.
