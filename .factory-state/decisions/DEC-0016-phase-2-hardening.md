# Decision

## Metadata

- Project: langgraph-studio
- Decision ID: DEC-0016
- Task ID: TASK-0019
- Status: Accepted (owner asked to resolve the phase-2 open issues; details chosen KISS by the agent)
- Date: 2026-10-17

## Decisions

1. **Active time**: `duration_ms` = wall time minus the gaps from each `run_waiting` event to the next event. This is derived from events, so there is no new column.
2. **Expiry**:
   - `STUDIO_WAIT_TTL` seconds, default 7 days, `0` = never. Measured from when the run started waiting (`runs.ended` of the waiting record).
   - Expired runs get a `run_expired` event and status `expired`.
   - A lifespan sweep runs every 60 s, plus a lazy check on resume and pending. Resuming an expired run returns `RUN_EXPIRED` (410 Gone).
3. **Pending badge**: polls `/api/runs/pending` every 30 s and on window focus. No push channel (KISS).
4. **Webhook signatures**:
   - Format: `X-Studio-Signature: t=<unix>,v1=<hex HMAC-SHA256(secret, "<t>.<raw body>")>`, Stripe-style so receivers know it. Receivers should use a 5-min tolerance.
   - The per-token secret is `whsec_…`, shown once and stored Fernet-encrypted, because the server must be able to sign.
   - Tokens created earlier (only in unmerged PR #14) have no secret, so their callbacks stay unsigned. No backfill, because a secret nobody has seen is useless.
5. **Rate limit**:
   - A fixed window per token, applied only to *starting* runs; polling is not limited. Defaults: 60 per 60 s.
   - Uses Redis `INCR` + `EXPIRE`, or a per-process in-memory counter. Returns `RATE_LIMITED` (429) with `Retry-After`.
6. **Reliable queue**:
   - Redis `BLMOVE` into a per-worker processing list, `LREM` ack after the run is recorded, and a heartbeat key with a 30 s TTL.
   - On worker start, jobs in processing lists whose worker has no heartbeat are requeued at the head as `recovered`; the worker re-runs them from the start (at-least-once).
   - The in-memory queue is documented as dev-only. No Celery or Streams (KISS).
7. **Sync wait**: capped at `STUDIO_SYNC_WAIT_MAX` (30 s), then 202 with `poll_url` and a `Location` header. Async responses also carry `poll_url`.
8. **DNS rebinding**:
   - The host is resolved once at delivery and *every* returned address must be public.
   - The connection goes to the first address, with the `Host` header and TLS SNI/certificate check on the original name (httpx `sni_hostname`).
   - Redirects are not followed.
9. **Versions**:
   - Pagination: `limit`/`offset` (max 200) returning `{items,total,limit,offset}`.
   - Retention: `STUDIO_VERSION_KEEP` (0 = all) keeps the newest N plus any version referenced by a run.
   - Restoring identical content returns `unchanged`.
   - Version-number conflicts are retried 3 times.
   - The unsaved-changes warning compares the editor's serialized graph with a snapshot taken after load/save.
10. **Migration lock**: `pg_advisory_xact_lock` in the migration transaction (Postgres) and an exclusive `fcntl` lock on `<db>.migrate.lock` (SQLite file DBs; no-op on Windows/in-memory).
11. **Prices**: built-in table, overridden by `STUDIO_PRICES_FILE` and then by `STUDIO_PRICES` (JSON `{prefix: [in, out]}` per 1M tokens). Re-read when the env value or the file's mtime changes; invalid entries are ignored with a warning.
12. **Tracing**:
    - Spans stay emitted at run end (documented).
    - When our LangSmith OTLP exporter is configured, LangChain's native tracer is disabled: `LANGSMITH_TRACING_V2=false`, which outranks `LANGSMITH_TRACING` and is inherited by import sandboxes, plus `langsmith.configure(enabled=False)`.
13. **Async Redis**:
    - Event-loop calls (`RunBus.astart/apublish`, the rate limiter) use `redis.asyncio`, with one client per loop.
    - `RunBus.finish` at run end runs on a worker thread, submitted at once and shielded, so a closing loop cannot drop it (TASK-0060; `afinish` was removed).
    - Blocking calls (job `BLMOVE`, `is_cancelled` polled from the run thread, REST cancel in threadpool routes) stay synchronous in threads.

## Deferred

> Resolved in TASK-0020 (DEC-0017), except exactly-once execution, which stays at-least-once by design (see DEC-0017, Idempotency limits).

- Push/e-mail notifications for waiting runs.
- A webhook delivery log, a retry queue, and secret rotation.
- Exactly-once job execution: at-least-once with a `recovered` re-run is accepted.
- Metrics export (OTel metrics / Prometheus).
- Streaming spans during a run.
