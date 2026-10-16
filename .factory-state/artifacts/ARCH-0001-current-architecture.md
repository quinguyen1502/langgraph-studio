# Architecture Artifact

## Metadata

- Project: langgraph-studio
- Architecture ID: ARCH-0001
- Status: Observed (documents existing implementation)
- Owner: Thái Quí Nguyễn
- Created: 2026-10-16
- Updated: 2026-10-16
- Related Requirements: REQ-0001

## Context

Inspected: `backend/app/{main,compiler,auth,importer,example}.py`, `backend/app/sandbox/runner.py`, `frontend/src/**`, `dev.sh`, `backend/tests/`.

## Decision Or Proposal

- Frontend SPA (Vite + React + TS, @xyflow/react, Tailwind v4, shadcn/ui, react-router) served by Vite dev server on :5173, proxying `/api` and `/ws` to the backend.
- Backend FastAPI on :8000. Workflow JSON `{nodes, edges, state}` stored in SQLite (`workflows`, `runs`, `users`).
- `compiler.py` validates the JSON and builds a `langgraph.StateGraph` (TypedDict from state schema; Condition nodes → `add_conditional_edges` keyed on edge labels).
- Runs: WebSocket `/ws/run?token=` → worker thread executes `graph.stream(stream_mode="updates")` → per-node events (`node_started`, `node_finished{duration_ms, delta}`, `run_finished`, `error`) → stored in `runs`.
- Imports: `importer.py` clones/unzips into `backend/imports/<job>/`, creates a per-import venv with uv, and executes `sandbox/runner.py` in a subprocess (inspect via `get_graph(xray=True)`; run via `astream(stream_mode=["debug","values"])`). Imported workflows carry server-side `source` metadata; runs always execute the original graph.
- Auth: PBKDF2-SHA256 password hashes, HS256 JWT (24h), bearer header for REST, query token for WebSocket.

## Rationale

Simplest stack satisfying the MVP brief (internal use + learning); SQLite and in-process worker threads avoid infrastructure.

## Alternatives Considered

- Option: Celery/Redis run queue
  - Benefits: horizontal scaling, durable jobs
  - Tradeoffs: extra infrastructure for MVP (tracked in REQ-0008)
- Option: container sandbox for imports
  - Benefits: real isolation
  - Tradeoffs: requires container runtime (tracked in REQ-0009)

## Boundaries And Interfaces

- REST: `/api/auth/*`, `/api/me`, `/api/workflows*`, `/api/import*`, `/api/tools`, `/api/health`
- WebSocket: `/ws/run?token=`
- Subprocess contract: `runner.py inspect|run <repo> <file:var>` emitting JSON lines

## Data Or State Considerations

- Import jobs are in-memory (lost on restart); import directories persist on disk.
- SQLite schema migrated inline at startup.

## Quality Attributes

- Security: imported code is not sandboxed beyond subprocess/venv/env-trim/timeout (documented risk).
- Reliability: single process; no run cancellation.
