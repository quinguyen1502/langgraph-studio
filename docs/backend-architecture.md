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

## Database

- `DATABASE_URL` (SQLAlchemy URL) overrides `STUDIO_DB`; default `sqlite:///<STUDIO_DB or backend/studio.db>`. SQLite keeps WAL + 15 s busy timeout.
- Postgres-ready: `DATABASE_URL=postgresql+psycopg://…` (install a driver, e.g. `psycopg[binary]`); models use portable types (Text, Float). Not tested on Postgres in CI yet (REQ-0008 / TASK-0009).
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

## Porting PR #2 (TASK-0005 credentials) onto this structure

| PR #2 piece | Goes to |
|---|---|
| `credentials` table (raw `CREATE TABLE`) | `models/credential.py` + Alembic revision `0002_credentials` |
| `credentials.py` encryption (Fernet) | `core/crypto.py` |
| provider registry `PROVIDERS`, provider HTTP calls in `compiler.py` | `engine/llm.py` (`call_llm`) |
| CRUD + resolver | `repositories/credentials.py`, `services/credential_service.py` (`resolver(uid)`) |
| `/api/providers`, `/api/credentials*` | `api/routes/credentials.py` |
| resolver passed to `run_stream` | `RunPlan.events()` → `run_stream(wf, inp, resolve=…)` |
