# Decision Record

## Metadata

- Project: langgraph-studio
- Decision ID: DEC-0014
- Status: Accepted
- Owner: Thái Quí Nguyễn
- Created: 2026-10-16
- Updated: 2026-10-16
- Related Requirements: REQ-0004
- Related Architecture: ARCH-0001
- Related Tasks: TASK-0007

## Context

REQ-0004: external systems start runs with JSON input and get the result synchronously or by callback. Until now runs only executed in the API process that held the WebSocket. Open question: "Is a cron/schedule trigger also needed?"

## Decision

1. **No cron in this task** (REQ-0004 lists it as out of scope). A scheduler can call the same trigger endpoint later; nothing here blocks it.
2. **Per-workflow API tokens**: `workflow_tokens` table (migration `0005_api_triggers`).
   - Tokens look like `wft_<random>` and are shown once; only the SHA-256 is stored.
   - Each token is bound to one workflow and its owner. Revoking sets `revoked`.
   - A token is rejected with `TRIGGER_TOKEN_INVALID` (401) when it is missing, unknown, revoked, belongs to another workflow, or the workflow is no longer owned by the token's owner.
   - The owner manages tokens with a JWT: `GET/POST /api/workflows/{wid}/tokens`, `DELETE …/{tid}` (`TOKEN_NOT_FOUND`).
3. **Trigger**: `POST /api/hooks/workflows/{wid}/runs` with `Authorization: Bearer wft_…` (or `X-Workflow-Token`) and body `{input, mode: async|sync, callback_url?}`.
   - async → 202 `{run_id, status: queued}`.
   - sync → waits up to `STUDIO_RUN_TIMEOUT + 5` s and returns `{run_id, status, final_state, error, metrics, …}` (202 if still running).
   - `GET /api/hooks/workflows/{wid}/runs/{run_id}` polls the result.
   - Runs are stored with `runs.source = "api"` and shown with an API badge in history.
4. **Job queue + worker, same pattern as RunBus (KISS)**:
   - `services/job_queue.JobQueue` has two implementations: `InMemoryJobQueue` (REDIS_URL unset) and `RedisJobQueue` (Redis list, LPUSH/BRPOP).
   - `services/run_worker.RunWorker` executes jobs with the same `RunService.execute` as the WebSocket (bus cancel, telemetry and metrics included). It runs inside the API process (`STUDIO_WORKER=1`, default; `STUDIO_WORKER_CONCURRENCY=2`) and/or as `python -m app.worker`. Compose runs a dedicated `worker` service and sets `STUDIO_WORKER=0` on the API.
   - Queued runs are pre-created with status `queued`, so cancel works before pickup. Sync mode polls the shared runs table, so it works across processes.
   - WebSocket runs are unchanged (still executed in the socket's process, so streaming stays direct).
5. **Result webhook**: on completion, POST the result JSON to `callback_url` with header `X-Studio-Event: run.finished`, two attempts with a 10 s timeout.
   - Only `http(s)` is allowed. Hosts resolving to private, loopback, link-local or reserved addresses are refused (`CALLBACK_URL_INVALID`) unless `STUDIO_ALLOW_PRIVATE_CALLBACKS=1` (SSRF guard).
   - Webhooks are not signed yet.

## Consequences

- Without Redis, a queued job lives only in the API process memory (lost on restart; the row stays `queued`).
- Human nodes work for API runs (status `waiting`); they are resumed from the UI.
