# QA Report

## Metadata

- Project: langgraph-studio
- QA ID: QA-0029
- Task ID: TASK-0015
- QA Owner: Grok (agent QA). Owner sign-off is still pending.
- Created: 2026-10-18
- Updated: 2026-10-18
- Outcome: pass with follow-up

## Validation Scope

Commit `4d3813b` on `factory/task-0015-run-repo-imports-inside-a-container-sandbox` (the review move; implementation is `12c9606`). Tool policy `commands` is empty, so the task's own validation plan was used: backend pytest and the frontend build. The live Docker acceptance from earlier on 2026-10-18 was not repeated. Review artifact: REV-0029.

## Acceptance Criteria Coverage

- Criterion: With `STUDIO_ENABLE_IMPORT` unset, `/api/import*` is unavailable and the Import button is hidden; with it set to `1`, current behaviour works.
  - Result: pass
  - Evidence: `backend/tests/test_import_sandbox.py` (anonymous POST is 401 `AUTH_REQUIRED`; authenticated POST, GET, and finalize are 404 `IMPORT_DISABLED`; health `import_enabled` follows the flag). `Workflows.tsx` renders `ImportDialog` only when `creates && importsOn`, and `importsOn` starts false. Browser check on 2026-10-18: flag off, `#import-btn` count 0 at 1280x800 and 390x844, authed POST 404 `IMPORT_DISABLED`; flag on, button visible, URL tab and zip file input shown. Full suite on this commit still passes `tests/test_import.py` under `STUDIO_IMPORT_RUNTIME=subprocess`.

- Criterion: Import and run of `new-langgraph-project` succeed inside the container with identical events.
  - Result: pass with a gap on the word "identical"
  - Evidence: Live Docker Desktop run on 2026-10-18 (`python:3.12-slim`). Nodes `__start__`, `call_model`, `__end__`. Final state `output from call_model. Configured with studio`. Inspect and run launch the same `backend/app/engine/sandbox/runner.py` (staged to `/opt/studio-runner`). No subprocess-versus-Docker log of the same input was saved.

- Criterion: Imported code cannot read files outside its import directory or the server environment.
  - Result: pass for the live probe and the argv/env unit tests
  - Evidence: Live probe wrote inside the job directory, and reading a host sentinel raised `FileNotFoundError`. `JWT_SECRET` and `STUDIO_DB` were empty in the sandbox. `test_import_sandbox.py` checks that `sandbox_env` drops server secrets, and that `build()` mounts only the job directory read-write plus the runner read-only, with `--read-only` and `--cap-drop ALL`. The image root is still readable inside the container. That is the image filesystem, not the host.

- Criterion: A run exceeding limits is killed and reported as an error event.
  - Result: pass for the time limit; memory limit not executed live
  - Evidence: Live run, `STUDIO_RUN_TIMEOUT=12`, a 30s sleep, last event `Sandbox stopped (time limit (12s)).`. `failure_event` maps a timeout and exit 137 in `test_import_sandbox.py`. `build()` sets `--memory`, `--memory-swap` (same value), `--cpus`, and `--pids-limit`. No live OOM was run.

- Criterion: REQ-0009 in-scope items also called for by the task (job persistence, cleanup, size cap, explicit secrets, read-only base).
  - Result: pass by inspection and unit tests
  - Evidence: `job.json` persist/reload, dead in-progress job becomes "Import interrupted by a restart", `mark_kept`, and age-based cleanup are covered in `test_import_sandbox.py`. `_dir_size` skips `.git` and rejects an over-cap tree. Secret names are filtered by `allow_secret`. README and `.env.example` document the flag as experimental.

## UX And Accessibility Coverage

- Criterion: Import button hidden when the feature is off; no new widget, colour, or untranslated string.
  - Result: pass
  - Evidence: `importsOn` defaults false, so the button does not flash on. The control is the existing `ImportDialog`. `IMPORT_DISABLED` exists in `frontend/src/locales/en.json` and `vi.json`. No new hard-coded colour. Light/dark screenshots were not taken; the change does not restyle the dialog. Desktop and 390px checks were done on 2026-10-18.

## Checks Performed

- `cd backend && /tmp/lgs-qa-venv/bin/python -m pytest -q --tb=line` on commit `4d3813b`: 278 passed, 10 skipped, 256 warnings, 97.65s. Exit 0. Python 3.12. `backend/.venv` is Python 3.14 and was not used.
- `cd frontend && npm run build` (`tsc -b && vite build`) on the same commit: exit 0. Existing Vite native-config warning and the chunk-size warning only.
- Live Docker import, isolation probe, and time-limit kill: 2026-10-18, recorded on the task. Not repeated for this QA.
- `factory ids check --ref origin/develop`: unique. `factory ids check --all-refs` still fails on the old `main` task names from before DEC-0007. Not caused by this task.

## Defects

- None found in this pass.

## Gaps Or Untested Areas

- Live cgroup OOM (exit 137) was not run.
- No saved side-by-side event log against a subprocess run of `new-langgraph-project`.
- Compose was not brought up with `STUDIO_IMPORT_HOST_DIR` and the socket gid. The live path was `./dev.sh` on the host with Docker Desktop.
- Postgres + Redis suite, full Playwright e2e, and a fresh light/dark screenshot set were not run.
- README checkpoint paragraph still describes the import runner as a subprocess.

## Residual Risk

- Turning the flag off selects the host subprocess for graphs imported earlier, including a trimmed but still privileged environment.
- The Compose Docker socket is mounted even while import is disabled.
- Default run network is `bridge`. Install is always `bridge`.
- `STUDIO_RUN_TIMEOUT` for imports is read when `repo_import` is imported (default 300), not from `config.run_timeout()` (120).

## Assumptions

- Docker Desktop on this Mac is the runtime the owner accepted for the task. gVisor and Firecracker were not required.
- The 2026-10-18 live log still describes this commit. The later edits (`lexists`, Docker Desktop CLI lookup) are inside `12c9606`, which is the implementation commit under `4d3813b`.

## Required Follow-Up

- Owner review of PR #33. This QA does not mark the task done and does not merge.
- Optional: Compose profile so the socket is absent when import is off; a live OOM; a paired event log; fix the stale subprocess sentence in the README checkpoint section.

## QA Decision

Conditionally passed with documented risk. Outcome for the task record: pass with follow-up. Not passed to done.
