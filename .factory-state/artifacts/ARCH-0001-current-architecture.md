# Architecture Artifact

## Metadata

- Project: langgraph-studio
- Architecture ID: ARCH-0001
- Status: Observed (documents existing implementation)
- Owner: Thái Quí Nguyễn
- Created: 2026-10-16
- Updated: 2026-10-16 (TASK-0017 layering)
- Related Requirements: REQ-0001

## Context

Inspected: `backend/app/**` (layered since TASK-0017, DEC-0009), `frontend/src/**`, `dev.sh`, `backend/tests/`.

## Decision Or Proposal

- Frontend SPA (Vite + React + TS, @xyflow/react, Tailwind v4, shadcn/ui, react-router) served by Vite dev server on :5173, proxying `/api` and `/ws` to the backend.
- Backend FastAPI on :8000, layered (DEC-0009, `docs/backend-architecture.md`): `api` routers → `services` → `repositories` (SQLAlchemy 2.0 ORM) / `engine` (LangGraph); `core` config/security/errors; `schemas` DTOs. Workflow JSON `{nodes, edges, state}` stored in `workflows`, `runs`, `users` (SQLite default, `DATABASE_URL` for others).
- `engine/validator.py` + `engine/compiler.py` validate the JSON and builds a `langgraph.StateGraph` (TypedDict from state schema; Condition nodes → `add_conditional_edges` keyed on edge labels).
- Runs: WebSocket `/ws/run?token=` → worker thread executes `graph.stream(stream_mode="updates")` → per-node events (`node_started`, `node_finished{duration_ms, delta}`, `run_finished`, `error`) → stored in `runs`.
- Imports (TASK-0015): `engine/repo_import.py` clones or unzips on the API host into `STUDIO_IMPORT_DIR` (default `~/.langgraph-studio/imports/<job>/`). With `STUDIO_ENABLE_IMPORT=1` the default runtime is Docker (`engine/sandbox/container.py`): install, inspect and run mount only that job directory. `STUDIO_IMPORT_RUNTIME=subprocess` keeps the host venv subprocess for tests. Imported workflows carry server-side `source` metadata; runs always execute the original graph. The flag defaults off (`IMPORT_DISABLED`).
- Auth: PBKDF2-SHA256 password hashes, HS256 JWT (24h), bearer header for REST, query token for WebSocket.

## Layer Diagram (TASK-0017)

```
api/routes ─► services ─► repositories ─► models (SQLAlchemy) ─► DB (SQLite | DATABASE_URL)
                  │                         migrations (Alembic)
                  └────► engine (validator, compiler, nodes, llm, tools, runtime, repo_import)
core (config, security, errors) ◄── all layers      schemas (Pydantic) ◄── api
```

## Rationale

Simplest stack satisfying the MVP brief (internal use + learning); SQLite and in-process worker threads avoid infrastructure.

## Alternatives Considered

- Option: Celery/Redis run queue
  - Benefits: horizontal scaling, durable jobs
  - Tradeoffs: extra infrastructure for MVP (tracked in REQ-0008)
- Option: container sandbox for imports
  - Benefits: real isolation
  - Tradeoffs: requires a container runtime (REQ-0009). TASK-0015 implements this with Docker. gVisor and Firecracker stay out of scope.

## Boundaries And Interfaces

- REST responses use the envelope `{success, data, error{code,message,details?}}` (DEC-0010, `docs/api-errors.md`). Error codes come from `core/errors.py` `CATALOG`. The frontend translates codes with react-i18next (`frontend/src/locales/{en,vi}.json`).

- REST: `/api/auth/*`, `/api/me`, `/api/workflows*`, `/api/import*`, `/api/tools`, `/api/health`
- WebSocket: `/ws/run?token=`
- Telemetry (`services/telemetry.py`, DEC-0012): one OTel trace per run (root `run` + one span per node), exported over OTLP (`OTEL_*`) and/or to LangSmith (`LANGSMITH_API_KEY` + `LANGSMITH_TRACING`); no-op otherwise. Final WS event `run_summary` {metrics, trace_id, trace_url}.
- Human-in-the-loop (TASK-0006, DEC-0013): node type `human` pauses a run (status `waiting`, checkpoint in `runs.checkpoint`). Resume over WS `{resume_run_id, response}` (owner only); `GET /api/runs/pending`.
- API triggers (TASK-0007, DEC-0014): per-workflow tokens (`workflow_tokens`), `POST /api/hooks/workflows/{wid}/runs` (async/sync, `callback_url`), `JobQueue` (memory or Redis list) + `RunWorker` (in the API process and/or `python -m app.worker`); `runs.source` ui|api.
- Workflow versions (TASK-0008, DEC-0015): `workflow_versions` (immutable snapshot per changing save, author + timestamp); restore = new latest version; `runs.workflow_version` records the version that ran (NULL = unsaved edits).
- Hardening (TASK-0019, DEC-0016): HITL active time + expiry; signed, rate-limited, DNS-pinned webhooks; reliable Redis queue (processing lists, ack, heartbeat recovery); version pagination/retention; locked startup migrations; price overrides; async Redis on the event loop.
- Deferred hardening (TASK-0020, DEC-0017): notifications (in-app, SMTP, notify webhook); webhook delivery log with queued exponential-backoff retries, redelivery and secret rotation with grace; leased Redis jobs with a periodic reaper (replaces heartbeat); recovered runs resume from the last LangGraph checkpoint; live per-node spans and optional OTLP metrics.
- Effectively-once (TASK-0021, DEC-0018): idempotency keys + node-result ledger for side-effect nodes; LangGraph superstep checkpoints (fan-out, imported graphs via serialized saver state); fencing tokens (`runs.lease_gen`); lost segment roots exported with their original span id; live notification push (Redis pub/sub / in-memory, WebSocket), HTML e-mail, per-user preferences.
- Run control: `POST /api/runs/{id}/cancel` (TASK-0009, works across API workers when Redis is configured)
- RunBus (`services/run_bus.py`): `InMemoryRunBus` (default) or `RedisRunBus` (`REDIS_URL`): run registry, cancel flags, event fan-out on `run:{id}:events` (DEC-0011)
- Subprocess contract: `runner.py inspect|run <repo> <file:var>` emitting JSON lines

## Data Or State Considerations

- Import jobs persist as `job.json` in the job directory and reload on startup. An in-progress job whose pid is gone becomes an error. Finalized workspaces are kept; others are deleted after `STUDIO_IMPORT_MAX_AGE_HOURS`.
- Database: SQLite file by default; Postgres via `DATABASE_URL` (psycopg 3), tested in CI (TASK-0009, DEC-0011).
- `runs` has per-run summary metrics (`duration_ms`, `tokens_in`, `tokens_out`, `cost_usd`, `error_count`, `trace_id`; migration `0003_run_metrics`, TASK-0010).
- Schema managed by Alembic (`backend/app/migrations`, `0001_initial` = MVP schema, adopts pre-Alembic files); `alembic upgrade head` runs at startup.

## Quality Attributes

- Security: with `STUDIO_ENABLE_IMPORT=1` and the Docker runtime, imported code runs in a read-only container that sees only its job directory and explicitly injected secrets. The subprocess runtime (`STUDIO_IMPORT_RUNTIME=subprocess`, also the default while the flag is off) is still only a venv plus env trim and a timeout. The Compose Docker socket is root-equivalent on the host.
- Reliability: cooperative cancel + timeout per run (TASK-0004). WebSocket runs execute in the API process holding the socket; API-triggered runs go through the job queue to any worker (TASK-0007). Redis carries cancel signals, events and jobs between processes.
- Deployment: `docker-compose.yml` (postgres, redis, api, web/nginx) with healthchecks and volumes (TASK-0009).
