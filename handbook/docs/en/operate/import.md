# Import a LangGraph repo

Import turns an existing Python LangGraph project into a workflow you can run
and trace in the studio. The graph runs as the **original** code, inside a
Docker sandbox.

!!! warning "Experimental, off by default"
    Import is off until `STUDIO_ENABLE_IMPORT=1`. While it is off,
    `/api/import*` returns `404 IMPORT_DISABLED` and the **Import repo** button
    stays hidden. `GET /api/health` reports `import_enabled`.

## Import

On **Workflows**, **Import repo** takes a public GitHub URL (with an optional
branch and subdirectory) or a zip. The dialog shows fetching, installing,
inspecting and ready. Pick one graph and create a workflow.

What happens (`backend/app/engine/repo_import.py`,
`backend/app/engine/sandbox/container.py`, `backend/app/engine/sandbox/runner.py`):

1. `git clone --depth 1`, or a zip extract that rejects zip-slip paths, into
   `~/.superstep/imports/<job_id>/` (`STUDIO_IMPORT_DIR`). This runs on
   the API process; the API image includes `git`.
2. `python -m venv` and `pip` run **inside Docker** (`STUDIO_IMPORT_IMAGE`,
   default `python:3.12-slim`). Packages come from `pyproject.toml` /
   `setup.py` (`pip install -e .`) or `requirements.txt`, always plus
   `langgraph` and `python-dotenv`.
3. Graphs come from `langgraph.json`, or from a scan for `StateGraph` and
   `x = ….compile(…)`. The scan only reads files.
4. `runner.py inspect` calls `graph.get_graph(xray=True)` with
   `--network none` (120 s, `STUDIO_INSPECT_TIMEOUT`).
5. `__start__` / `__end__` become Start / End. Other nodes become read-only
   Code nodes, laid out with dagre.

## Run

A run executes the original graph through `runner.py run` (`graph.astream`).
Events become `node_started` / `node_finished`. Put runtime context in the
input under `__context__`. A missing key named in `.env.example` is reported
on the error. A timeout or an out-of-memory exit (137) is one `error` event,
for example `Sandbox stopped (time limit (12s)).`

If the imported graph has no checkpointer, the runner attaches an in-memory
saver and sends a serialised checkpoint to the server, so a recovered run
starts a new container from it. State that cannot be serialised, or is larger
than 2 MB, starts again from the beginning. There is no ledger inside the
imported repo.

## The sandbox

| Control | Setting |
| --- | --- |
| Filesystem | Read-only root; only the job directory is mounted read-write; a read-only copy of `runner.py` at `/opt/studio-runner`; tmpfs `/tmp` |
| Privileges | All capabilities dropped, `no-new-privileges` |
| Memory | `STUDIO_IMPORT_MEMORY` (default `1g`, swap equal to memory) |
| CPU | `STUDIO_IMPORT_CPUS` (default `1`) |
| Processes | `STUDIO_IMPORT_PIDS` (default 256) |
| Network | Install: `bridge`. Inspect: `none`. Run: `STUDIO_IMPORT_NETWORK` (`bridge` or `none`, default `bridge`) |
| Environment | Not the server's. Only names declared in `.env.example` that exist on the server, plus `STUDIO_IMPORT_SECRETS`. `JWT_SECRET`, `DATABASE_URL`, `REDIS_URL` and every `STUDIO_*` name are never injected. |
| Time | `STUDIO_RUN_TIMEOUT`, read at process start (default 300 s for import runs) |

`localhost` inside the sandbox is the container. There is no silent fallback
to a subprocess while the runtime is Docker. `STUDIO_IMPORT_RUNTIME=subprocess`
exists for tests and machines without Docker; it is the same OS user as the
API and is not a sandbox.

## Under Compose

Compose mounts `/var/run/docker.sock` into `api` and `worker`, which is
root-equivalent on the Docker host. Do not enable import on a host you do not
trust. Before `docker compose up`:

```bash
export STUDIO_ENABLE_IMPORT=1
export STUDIO_IMPORT_HOST_DIR="$PWD/.imports"   # absolute host path of the bind mount
mkdir -p "$STUDIO_IMPORT_HOST_DIR"
```

Without `STUDIO_IMPORT_HOST_DIR` the daemon mounts the in-container path and
the sandbox fails. On Linux, if the container user cannot open the socket, set
`STUDIO_DOCKER_GID="$(stat -c %g /var/run/docker.sock)"`. If `docker` is not on
`PATH`, the API uses Docker Desktop's CLI at
`/Applications/Docker.app/Contents/Resources/bin/docker`.

## Housekeeping

Jobs persist as `job.json`. A restart marks an in-progress job as
`Import interrupted by a restart` when its pid is gone. A workflow created
from a job is marked `keep` and is not cleaned up. Other job directories older
than `STUDIO_IMPORT_MAX_AGE_HOURS` (default 72, `0` disables cleanup) are
deleted when the next import starts. A source tree over
`STUDIO_IMPORT_MAX_BYTES` (default 200 MB, `.git` excluded) is rejected.

## Not supported

Private repos, JS monorepos, complex `langgraph.json` files, gVisor and
Firecracker.

Checked against `langchain-ai/new-langgraph-project` (runs without a key) and
`langchain-ai/react-agent` (imports and shows its loop; a run asks for the
missing provider key).
