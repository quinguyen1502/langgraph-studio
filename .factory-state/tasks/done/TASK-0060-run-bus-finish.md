# Task

## Metadata

- Project: superstep
- Task ID: TASK-0060
- Status: done (PR #76, REV-0056, QA-0056)
- Phase: release
- Owner: Thái Quí Nguyễn
- Created: 2026-10-20
- Updated: 2026-10-20
- Requirement IDs: none (a reliability fix)
- Design IDs: none
- Architecture IDs: DEC-0009, DEC-0016

## Objective

Clear a run's run bus entry (`run:{id}:owner`, `run:{id}:cancel`) when the run ends, even if the handler is cancelled
and its event loop closes at that moment. This is the follow-up from REV-0055.

## Cause

- `RunService.execute` ended with `finally: await asyncio.shield(self.bus.afinish(rid))`.
- `afinish` is a coroutine, so `shield` wraps it in a task that only starts on the next loop iteration. On the Redis
  bus without an async client, it also queued `finish` with `asyncio.to_thread`, which a cancel drops while no thread
  has picked it up.
- When the loop closes right after the handler is cancelled (uvicorn shutdown, Starlette TestClient leaving
  `websocket_connect`), that work never ran.
- Effect: the run was recorded, but its owner key stayed until its 24 h TTL. Until then a REST cancel took the
  finished run for one still running elsewhere and did not change its stored status. With the in-memory bus the entry
  stayed until the process restarted. No data was lost.

## Fix

- `execute` clears the entry with `_write_in_thread(self.bus.finish, rid)`, the TASK-0059 helper: `finish` is
  submitted to the executor straight away and shielded, so a cancel cannot drop it.
- `RunBus.afinish` has no caller left and is removed from the protocol and both buses. `finish` is a single Redis
  `DELETE` on a worker thread, so the loop is still never blocked. DEC-0016 point 13 is updated to match.

## Scope

### In Scope

- `services/run_service.py`, `services/run_bus.py`, their tests and DEC-0016.

### Out Of Scope

- `settled()` (queueing an API run's callback), which still uses `asyncio.to_thread`. See the follow-up in REV-0056.

## Related Artifacts

- Earlier: TASK-0059 (PR #73), REV-0055 (follow-up), QA-0055
- Architecture: `docs/backend-architecture.md` (DEC-0009), DEC-0016

## Acceptance Criteria

- A regression test reproduces the lingering entry on the old code and passes with the fix.
- The backend suite passes on SQLite and on Postgres 17 + Redis 7, locally and in CI.

## Validation

- `tests/test_core_hardening.py::test_cancelled_run_leaves_the_run_bus_when_the_loop_shuts_down`, run 3 times before
  and after the fix.
- Full backend suite on Python 3.12 (SQLite) and on Postgres 17 + Redis 7.
