# Backend architecture (TASK-0017, DEC-0009)

```
            HTTP / WebSocket
                  │
   api/routes/*  (controllers: parse request, call service, shape response)
   api/deps.py   (DI: Database singleton, services, current_user, body limit)
   api/error_handlers.py (DomainError → HTTP status, readable 422)
                  │
   services/*    (business rules: ownership, naming, auth, run lifecycle, import)
        │                         │
   repositories/*            engine/*  (LangGraph: validator, compiler, nodes, llm, tools,
   (SQLAlchemy queries)                 runtime, limits, repo_import + sandbox runner)
        │
   models/*  (SQLAlchemy 2.0 typed Mapped models, Database: engine/session/migrate)
   migrations/ (Alembic; 0001_initial = MVP schema)
                  │
   core/*  (config/env vars, security: hashing + JWT, DomainError types, logging) — used by all
   schemas/* (Pydantic DTOs) — used by api
```

## Import rules (enforced by `tests/test_layers.py`)

| Layer | May import | Must not import |
|---|---|---|
| `core` | stdlib, jwt | anything else in `app`, FastAPI |
| `engine` | `core` | models, repositories, services, api, FastAPI |
| `models` | `core` | repositories, services, api, engine |
| `schemas` | pydantic | models, repositories, services, api |
| `repositories` | `models`, `core` | services, api, FastAPI |
| `services` | repositories, engine, models, core | api, FastAPI |
| `api` | everything | — |

- Services raise `core.errors` (`BadRequest`, `NotFound`, `Forbidden`, `Conflict`, `Unauthorized`, `TooLarge`); only `api/error_handlers.py` maps them to HTTP.
- Repositories hold no rules; each method opens its own short session (safe from the run worker thread).
- Service unit tests use in-memory fake repositories (`tests/test_services.py`).

## Responses and errors (DEC-0010)

- Every REST response is the envelope `{success, data, error}`. Routes return plain data; `EnvelopeResponse` (the FastAPI default response class) wraps it.
- Services raise `AppError("CODE", details=…, **params)`; codes and messages live only in `core/errors.py` `CATALOG`. `api/error_handlers.py` is the only place that builds error responses. Format and code catalog: `docs/api-errors.md`.
- Engine messages (validator, node errors) are English free text carried in `details` / `errors`.

## Database

- `DATABASE_URL` (SQLAlchemy URL) overrides `STUDIO_DB`; default `sqlite:///<STUDIO_DB or backend/studio.db>`. SQLite keeps WAL + 15 s busy timeout.
- Postgres: `DATABASE_URL=postgresql://…` (normalised to `postgresql+psycopg://`; `psycopg[binary]` is a dependency). Models use portable types (Text, Float). CI runs the whole suite on Postgres 17 + Redis 7, and `tests/test_db_postgres.py` migrates a throwaway database (TASK-0009, DEC-0011).
- Startup runs `alembic upgrade head` programmatically (`services/seed.bootstrap`), then seeds the demo user and example workflow.
- Revision `0001_initial` is idempotent: on a pre-Alembic SQLite file it creates only missing tables and adds `workflows.owner` if absent, then stamps the version. Existing data is untouched.
- CLI: `cd backend && .venv/bin/alembic upgrade head`; new migration: `.venv/bin/alembic revision -m "…"` (add `--autogenerate` after editing models).

## Where things live (old → new)

| Old | New |
|---|---|
| `main.py` (everything) | `main.py` (app factory) + `api/routes/{auth,meta,workflows,imports,runs_ws}.py`, `services/*`, `repositories/*`, `models/*` |
| `auth.py` | `core/security.py` (+ `api/deps.current_user`) |
| `compiler.py` | `engine/{errors,templating,tools,llm,validator,nodes,compiler,runtime}.py` |
| `limits.py` | `engine/limits.py` (values in `core/config.py`) |
| `importer.py`, `sandbox/runner.py` | `engine/repo_import.py`, `engine/sandbox/runner.py` |
| `example.py` | `engine/examples.py` |

## Credentials (TASK-0005, ported from PR #2: done)

| PR #2 piece | Goes to |
|---|---|
| `credentials` table (raw `CREATE TABLE`) | `models/credential.py` + Alembic revision `0002_credentials` |
| `credentials.py` encryption (Fernet) | `core/crypto.py` |
| provider registry `PROVIDERS`, provider HTTP calls in `compiler.py` | `engine/llm.py` (`call_llm`) |
| CRUD + resolver | `repositories/credentials.py`, `services/credential_service.py` (`resolver(uid)`) |
| `/api/providers`, `/api/credentials*` | `api/routes/credentials.py` |
| resolver passed to `run_stream` | `RunService.plan` binds `CredentialService.resolver(uid)` into `RunPlan`; `RunPlan.events()` → `run_stream(wf, inp, resolve)` → `node_fn` |

Secrets are encrypted in the service before they reach the repository; only `resolve()` decrypts, at run time.

## Run bus (TASK-0009, DEC-0011)

`services/run_bus.py` defines `RunBus` (start / finish / owner / request_cancel / is_cancelled / publish / ping):

- `InMemoryRunBus` when `REDIS_URL` is unset (one process).
- `RedisRunBus` when `REDIS_URL` is set: keys `run:{id}:owner` and `run:{id}:cancel` (24 h TTL), events published on `run:{id}:events`.

`RunService.execute` registers each run, publishes every event (best effort) and checks the cancel flag between steps. `POST /api/runs/{id}/cancel` → `RunService.cancel` (owner only, else `RUN_NOT_FOUND`). The bus is built once in `api/deps.get_run_bus`.

## Telemetry (TASK-0010, DEC-0012)

- `engine/usage.py`: price table and the usage record `{provider, model, tokens_in, tokens_out, tokens, cost_usd, estimated}`. `call_llm(..., on_usage)` reports it; `runtime.run_stream` attaches it to `node_finished.usage`. Mock runs are estimated and cost 0.
- `services/telemetry.py`:
  - `summarize(events)` gives the persisted run metrics;
  - `Telemetry.record_run(...)` builds the run's trace from event timestamps after the run;
  - `exporter_configs()` reads `OTEL_*` / `LANGSMITH_*`;
  - `trace_url()` fills `STUDIO_TRACE_URL`.
- `RunService.record` computes the metrics, records the trace (errors swallowed), stores both, and the socket gets a final `run_summary` event (not stored in `events`). History items carry `metrics`, `trace_id` and `trace_url`.
- Built once in `api/deps.get_telemetry`; tests inject `InMemorySpanExporter`.

## Human-in-the-loop (TASK-0006, DEC-0013)

- Engine:
  - `engine/nodes.py` `human` node raises `engine.errors.Interrupt` when it has no response.
  - `runtime.run_stream` turns that into `run_waiting` with a checkpoint {node, state}.
  - `run_stream(..., resume={node, value, state})` compiles with `entry=node` and feeds `value` to that node once (a loop back to it pauses again).
- Service:
  - `RunService.plan` sees `resume_run_id`, then `plan_resume` checks owner and `waiting` status and builds a plan with the same run id and the earlier events.
  - `record()` stores the checkpoint while waiting and clears it when the run ends; the trace is emitted only at the end.
- `runs.owner` (backfilled from workflows) and `runs.checkpoint` come from migration `0004_hitl`.

## API triggers and the job queue (TASK-0007, DEC-0014)

- `services/job_queue.py`: `JobQueue` with `enqueue` / `dequeue`. `InMemoryJobQueue` is the default; `RedisJobQueue` is a Redis list `studio:run-jobs` when `REDIS_URL` is set.
- `services/trigger_service.py`:
  - token create, list and revoke (only the SHA-256 is stored);
  - `authenticate`, which binds a token to its workflow and owner;
  - `start`, which pre-creates the run as `queued` (source `api`) and enqueues the job;
  - `wait`, the sync mode, which polls the runs table;
  - `run_result`, the public result shape shared by the REST response and the webhook;
  - `check_callback_url`, the SSRF guard.
- `services/run_worker.py`: `RunWorker` dequeues a job, skips it if it is no longer `queued`, sets it to `running`, then calls `RunService.plan` and `execute` (no socket: `send` is a no-op and cancel comes via the RunBus), then delivers the webhook.
  - Started by the app lifespan when `STUDIO_WORKER` is not `0`; `app/worker.py` runs it standalone.
- Routes: `api/routes/triggers.py`.

## Workflow versions (TASK-0008, DEC-0015)

- `models/workflow_version.py` + `repositories/workflow_versions.py`: one immutable row per version, unique `(workflow_id, version)`. Migration `0006_workflow_versions` backfills v1 for existing workflows and adds `runs.workflow_version`.
- `WorkflowService._write` is the single write path (save, rename, duplicate, import, seed, restore). It writes the workflow and then a new version only when the stored JSON changed.
- `services/workflow_diff.py` holds the pure functions:
  - `diff_workflows(a, b)` matches nodes and edges by id and state fields by name, and reports added, removed and changed (with before/after), plus `moved` for position-only changes;
  - `same_content` ignores the name and positions.
- `RunService.plan` tags a run with the latest version when the workflow it runs has the same content as that version, otherwise `NULL` (unsaved edits). A resume or cancel keeps the original tag.
- Routes live in `api/routes/workflows.py`: `/versions`, `/versions/diff`, `/versions/{n}`, `/versions/{n}/restore`.
