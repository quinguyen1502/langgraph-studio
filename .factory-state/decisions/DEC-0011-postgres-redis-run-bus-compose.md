# Decision Record

## Metadata

- Project: langgraph-studio
- Decision ID: DEC-0011
- Status: Accepted
- Owner: Thái Quí Nguyễn
- Created: 2026-10-16
- Updated: 2026-10-16
- Related Requirements: REQ-0008
- Related Architecture: ARCH-0001
- Related Tasks: TASK-0009

## Context

The MVP stores data in a SQLite file and keeps run state (cancel flags, events) inside one API process. REQ-0008 asks for Postgres, Redis and a Docker Compose deployment.

## Decision

1. **Database**: Postgres through `DATABASE_URL` with the psycopg 3 driver (`psycopg[binary]`). `postgres://` and `postgresql://` URLs are normalised to `postgresql+psycopg://`. The same Alembic revisions run on both backends. **SQLite stays the dev default** (answers the REQ-0008 open question).
2. **Redis** (`REDIS_URL`, optional) sits behind one small interface, `services/run_bus.RunBus`, with two implementations:
   - `InMemoryRunBus` when `REDIS_URL` is unset;
   - `RedisRunBus`, which keeps a run registry (`run:{id}:owner`), a cancel flag (`run:{id}:cancel`, both with a 24 h TTL) and publishes every run event on `run:{id}:events`.
   A run can be cancelled from any API worker with `POST /api/runs/{id}/cancel` (owner only, otherwise `RUN_NOT_FOUND`); the run ends with `run_cancelled` and `reason: "api"`.
3. **Not a job queue (KISS)**: runs still execute in the API process that holds the WebSocket. A Redis worker queue is deferred until there is a need (e.g. TASK-0007 webhooks with no socket).
4. **Deployment**: `docker-compose.yml` with `postgres`, `redis`, `api` (Python 3.12 slim, migrations at startup) and `web` (nginx serving the Vite build and proxying `/api` and `/ws`). Healthchecks on all four; named volumes `pgdata`, `redisdata`, `apidata`. Secrets come from `.env` (`JWT_SECRET`, `POSTGRES_PASSWORD` are required; `STUDIO_SECRET_KEY` optional).

## Consequences

- Health reports `database`, `run_bus` and `run_bus_ok`.
- CI gains a Postgres + Redis pytest job and a compose build + smoke job.
- One API container per stack: startup migrations are not guarded against concurrent upgrades.
