# Task

## Metadata

- Project: superstep
- Task ID: TASK-0059
- Status: done (PR #73, REV-0055, QA-0055)
- Phase: release
- Owner: Thái Quí Nguyễn
- Created: 2026-10-20
- Updated: 2026-10-20
- Requirement IDs: none (a reliability fix)
- Design IDs: none
- Architecture IDs: DEC-0009

## Objective

Make the CI job "Backend (pytest on Postgres 17 + Redis 7)" pass reliably. It fails on tests that expect a cancelled
or timed-out run to appear in the run history. Find out whether runs are really lost (a product bug) or the tests only
look too early, and fix the cause.

## Evidence

- `tests/test_core_hardening.py::test_disconnect_cancels_run`: `assert ([])`. The run list is still empty after a
  10 s loop.
  - On develop: 2026-10-19 13:01 (runs 39256632385, 39256695525) and 2026-10-20 00:14 (runs 39346391719, 39346400328).
  - Three runs on PR #69.
- `tests/test_core_hardening.py::test_timeout`: IndexError in `last_run`, so no run was recorded. Seen once on PR #69.
- `tests/test_approval_channels.py::test_api_run_resumed_from_*_sends_its_callback`: failed on develop (run
  39272873794, Postgres) and on PR #70 (Python 3.12, SQLite), with `['ok', 'pending'] == ['ok', 'ok']`.
- Locally (macOS, pgvector/pgvector:pg17 + redis:7, Python 3.12), nothing failed:
  - the cancel tests, run 15 times alone;
  - the full suite, run twice (once under extra load).

## Cause (found 2026-10-20)

- **A cancelled run could be lost. This is a product bug.**
  - In `RunService._execute`, the `except asyncio.CancelledError` path wrote the history with
    `await asyncio.shield(asyncio.to_thread(self.record, ...))`.
  - `asyncio.to_thread(...)` is a coroutine. `shield` wraps it in a task that only starts on the next loop iteration.
  - When the loop closes right after the handler is cancelled, every pending task is cancelled first, including that
    one. So `record` never ran and the run disappeared. The loop closes this way on uvicorn shutdown and when
    Starlette's TestClient leaves a `websocket_connect` block: it sends the disconnect, cancels the app task, then
    stops its portal.
  - Slower CI runners hit that window more often.
- **First cause: the cancel path.** Reproduced deterministically by a new test,
  `test_run_cancelled_while_the_loop_shuts_down_is_still_recorded`.
  - It cancels the handler task, runs one loop iteration, then cancels everything pending and closes the loop, as
    `asyncio.Runner` does.
  - Before the fix it failed 3 out of 3 runs. The server log showed the cancel path, but never `record`.
- **Second cause, the one CI kept hitting: the normal path after a disconnect.** CI diagnostics (round 2, PR #73)
  showed it.
  - Run `053adf25e0` took the normal path with `ended=disconnected` and was then cancelled at
    `await asyncio.to_thread(self.record, ...)`. `record` never started, and the run was not there 60 s later.
  - Cancelling a task that awaits `run_in_executor` also cancels the underlying `concurrent.futures.Future`. A work item
    still queued, with no free executor thread yet, is then dropped.
  - A new test reproduces it: `test_disconnected_run_is_recorded_when_the_write_waits_for_a_thread`. It keeps the only
    executor thread busy. On the old code it failed 3 out of 3 runs.
- **Fix:** both history writes of `_execute` go through `_write_in_thread`. It submits `record` to the executor
  immediately and returns it under `asyncio.shield`. Cancelling the awaiting task raises `CancelledError` there, but
  never cancels or drops the write. The cancel path still handles `StaleLease`, in `keep`.
- **`test_api_run_resumed_from_a_channel_sends_its_callback` was a test race, not the same bug.**
  - The mock webhook hook appends to `got` while the request is still in flight, and the worker marks the delivery
    `ok` only after the response.
  - The test now waits for both deliveries to be `ok` instead of reading the log once.

## Scope

### In Scope

- Diagnose with temporary prints in CI. They are removed before the PR is ready.
- Fix the cause in `services/run_service.py` (or wherever it is) with a regression test, if runs can be lost.
  Otherwise make the tests wait on the condition instead of a fixed time.
- The approval-callback test, if it has the same cause. Otherwise record it as a follow-up.

### Out Of Scope

- Behaviour changes beyond the fix.

## Related Artifacts

- Architecture: `docs/backend-architecture.md` (DEC-0009)
- Earlier: TASK-0058, PRs #69, #70 and #72 (merged with this job red, with the owner's approval)

## Acceptance Criteria

- The cause is identified and written here.
- CI on the PR passes the Postgres job on 3 consecutive runs, and the other jobs pass.
- No temporary diagnostics remain.

## Validation

- Backend suite on Python 3.12 (SQLite) and on Postgres 17 + Redis 7, locally and in CI.
