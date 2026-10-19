# Install

## Requirements

| For | Needs |
| --- | --- |
| Development | Python 3.12 or later, Node 20 or 22, Git |
| Compose stack | Docker with Compose v2 |
| Code mode, repo import | Docker on the API host |

## Local development

```bash
git clone https://github.com/quinguyen1502/langgraph-studio.git
cd langgraph-studio
./dev.sh
```

The first run creates `backend/.venv`, installs the backend with its dev
extras, and runs `npm install` in `frontend/`. Then it starts:

| Service | URL |
| --- | --- |
| UI (Vite) | <http://localhost:5173>, which proxies `/api` and `/ws` to the backend |
| API docs (OpenAPI) | <http://localhost:8000/docs> |

Sign in with the demo account `admin@example.com` / `admin123`. It is seeded
on start-up outside production, together with the **Customer Support**
example workflow.

Local development keeps its data in SQLite (`backend/studio.db`) and the run
bus in memory. Nothing else needs to be running.

!!! tip "No model key yet?"
    An LLM node with no credential and no `OPENAI_API_KEY` uses a deterministic
    offline mock, so every example runs without a provider. To use a real model,
    see [LLM providers](../operate/providers.md).

## Docker Compose

Compose runs Postgres 17 with pgvector, Redis 7, the API (it applies Alembic
migrations and seeds on start-up), a worker, and nginx serving the built UI.

```bash
cp .env.example .env   # set JWT_SECRET and POSTGRES_PASSWORD; never commit .env
docker compose up --build
python scripts/compose_smoke.py http://localhost:8080
```

The UI is at <http://localhost:8080> (`WEB_PORT`). The smoke script (it needs `httpx` and `websockets`) checks health, signs in
with the demo account and runs the seeded example over `/ws/run`.

Production settings, scaling workers and tracing are in
[Deploy with Compose](../operate/deploy.md).

## Check the install

```bash
curl -s http://localhost:8000/api/health
```

`data` reports `llm_mode`, `database` (`sqlite` or `postgresql`), `run_bus`
(`memory` or `redis`), `tracing` and `import_enabled`.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `Address already in use` for port 8000 | `dev.sh` always starts the API on 8000. Stop the other process, or start the backend by hand with another `--port` and set `STUDIO_API_PORT` for Vite. |
| The UI is not on 5173 | Vite moves to the next free port when 5173 is taken; `dev.sh` prints the URL it got. |
| Import errors after a pull | `dev.sh` installs only when `backend/.venv` or `frontend/node_modules` is missing. Run `backend/.venv/bin/pip install -e "backend[dev]"` and `npm install` in `frontend/`. |
| Code mode says the runtime is off | Code mode and repo import need Docker on the API host. See [Code runtime](../operate/code-runtime.md). |

## Next

[Quickstart](quickstart.md): build, run and trigger a workflow.
