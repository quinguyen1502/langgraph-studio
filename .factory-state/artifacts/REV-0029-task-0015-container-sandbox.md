# Review

## Metadata

- Project: langgraph-studio
- Review ID: REV-0029
- Task ID: TASK-0015
- Reviewer: Grok (agent review). Owner review on PR #33 is still pending.
- Created: 2026-10-18
- Updated: 2026-10-18
- Outcome: approved for QA

## Review Scope

Diff of `factory/task-0015-run-repo-imports-inside-a-container-sandbox` (`4d3813b`) against `origin/develop` (`92c5acf`). Three commits: move to doing, the Docker sandbox implementation, move to review.

Reviewed: `backend/app/engine/sandbox/container.py`, `backend/app/engine/repo_import.py`, `backend/app/services/import_service.py`, `backend/app/core/config.py`, `backend/app/core/errors.py`, `backend/app/api/routes/meta.py`, `backend/tests/test_import.py`, `backend/tests/test_import_sandbox.py`, `backend/Dockerfile`, `docker-compose.yml`, `.env.example`, `frontend/src/pages/Workflows.tsx`, both locale files, `docs/api-errors.md`, `docs/backend-architecture.md`, `README.md`, `roadmap.md`, `ARCH-0001`.

Acceptance criteria from the task and the in-scope items of REQ-0009. REQ-0009 status was not changed.

## Reference Artifacts

- `.factory-state/tasks/review/TASK-0015-run-repo-imports-inside-a-container-sandbox.md`
- `.factory-state/artifacts/REQ-0009-sandboxed-imports.md`
- `.factory-state/artifacts/ARCH-0001-current-architecture.md`
- `docs/backend-architecture.md` (DEC-0009)
- `docs/ui-conventions.md` (DEC-0008)
- `docs/api-errors.md`

## Findings

### Blocking

- No blocking findings.

### Non-Blocking

- With the flag off and `STUDIO_IMPORT_RUNTIME` unset, `import_runtime()` returns `subprocess`. A workflow imported while the flag was on later runs as the host user, and `sub_env()` still forwards `*_API_KEY` and `OPENAI_*` / `LANGSMITH_*` / `LANGCHAIN_*`. This is written down in `config.py`, ARCH-0001, and the README. It is weaker than REQ-0009 for graphs that already exist.
- `docker-compose.yml` mounts `/var/run/docker.sock` on `api` and `worker` whenever Compose is up, including when `STUDIO_ENABLE_IMPORT=0`. The app does not call Docker unless the runtime is Docker. The socket is still root-equivalent if that process is compromised. The README states this.
- Install always uses network `bridge`, so a malicious `setup.py` has egress. Inspect uses `none`. A run uses `STUDIO_IMPORT_NETWORK` (`bridge` or `none`, default `bridge`). Egress is operator-selected, and the default run is not deny-by-default.
- The live check killed a run on the time limit. It did not provoke a cgroup OOM. Exit 137 is mapped by `failure_event` and covered by a unit test.
- No side-by-side log of subprocess versus Docker events was saved. Inspect and run use the same `runner.py`. The live Docker run of `new-langgraph-project` produced `__start__`, `call_model`, `__end__`, and the expected state text.
- README section "Effectively-once" still says an imported workflow runs in a subprocess (the checkpoint paragraph). The import section above it describes the Docker path.
- ARCH-0001 body describes the sandbox. Its metadata `Updated` line still says 2026-10-16.
- The UI change only shows or hides the existing Import dialog. No new light/dark screenshots were taken. Browser checks confirmed the button is absent when the flag is off and present when it is on.

## Standards And Architecture Alignment

- Layers hold: the router calls `ImportService`, the service calls `repo_import`, and `container.py` imports only the standard library. The engine does not query the database. The flag check is in the service, so `start_job` stays callable from tests.
- `IMPORT_DISABLED` is in `core/errors.py` `CATALOG` (404), `docs/api-errors.md`, and `errors.IMPORT_DISABLED` in both `en.json` and `vi.json`.
- The Workflows change uses the existing shadcn `ImportDialog`, theme tokens already on the page, and no new literal UI string. The button starts hidden (`importsOn` defaults false) until `/api/health` reports `import_enabled`.
- No new delete flow. No new status colour.
- Git clone and zip extract stay on the host. Untrusted code starts at pip install. The sandbox argv drops all capabilities, sets `no-new-privileges`, a read-only root, equal memory and swap, cpu and pid limits, and a mode-0600 env file. `allow_secret` rejects `JWT_SECRET`, `STUDIO_SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`, `STUDIO_DB`, any `STUDIO_*`, lowercase names, and values that contain a newline or NUL.
- gVisor and Firecracker stay out of scope, matching the task assumption. REQ-0009 remains Proposed.

## Design Alignment

The user-facing change matches the task: the Import control is hidden while the flag is off, and the experimental flag is described in the README. No separate design artifact was required. Accessibility of the existing dialog was not changed.

## Validation Review

Developer validation recorded on the task is sufficient to enter QA, with the gaps listed above. This review did not treat a missing live OOM or a missing side-by-side event log as a failed acceptance criterion: the time limit was observed live, and the memory path has a unit test and the Docker flags. QA re-ran the suite and the frontend build on this commit; see QA-0029.

`factory ids check --ref origin/develop` passes. `factory ids check --all-refs` still reports the pre-DEC-0007 TASK id pairs on `main`. Those pairs are not introduced by this branch.

## Assumptions

- Integration branch for this PR is `develop`. `factory.yaml` and DEC-0002 still name `main`.
- Docker (including Docker Desktop on macOS) is the sandbox runtime for this task.
- `STUDIO_IMPORT_RUNTIME=subprocess` remains the test and CI path and is not a sandbox.

## Required Follow-Up

- None before QA. The non-blocking items above can stay as residual risk unless the owner wants a Compose profile for the socket, or wants runs to stay in Docker after the flag is turned off.
- Do not mark REQ-0009 or DEC-0032 accepted from this review.

## Review Decision

Approved for QA. No blocking findings. This is an agent review. It does not approve the PR for merge.
