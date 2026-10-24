# Sandbox service for Code nodes

[Tiếng Việt](sandbox.vi.md) · [Deploy guide](README.md) · [Environment variables](env-vars.md)

On a managed PaaS there is no Docker socket, so the all-in-one image runs Code nodes directly on the server, next
to the database and the secrets. The **sandbox service** moves that execution into a separate container that holds
none of the studio's secrets. The studio calls it over HTTP with a shared token.

```
studio (web / worker)  --HTTP + Bearer STUDIO_SANDBOX_TOKEN-->  sandbox service  -->  one process per call
JWT_SECRET, DATABASE_URL, credentials                            only the token        own uid, no env, limits
```

Image: `ghcr.io/quinguyen1502/superstep-sandbox` (built from `docker/studio-sandbox/Dockerfile`, published with the
main image).

## Enable it

On the sandbox service:

| Variable | Value |
|---|---|
| `STUDIO_SANDBOX_TOKEN` | A random string of 16+ characters (`openssl rand -hex 32`). Nothing else is needed. |
| `PORT` | Port to listen on (default 8080; Render sets it). |
| `STUDIO_SANDBOX_HOST` | Bind address (default `0.0.0.0`; `::` on Fly.io). |
| `STUDIO_CODE_MAX_SECONDS`, `STUDIO_CODE_MEMORY`, `STUDIO_CODE_CONCURRENCY` | Limits per call and calls at once (defaults 30 s, 256m, 4). |

On the studio (web and worker):

| Variable | Value |
|---|---|
| `STUDIO_CODE_RUNTIME` | `remote` |
| `STUDIO_SANDBOX_URL` | The service address, e.g. `http://sandbox:8080` (a bare `host:port` is fine). |
| `STUDIO_SANDBOX_TOKEN` | The same token. |

The **Code nodes** card in **Settings → Users** then shows "Sandbox service (remote)" and whether each language is
ready. Runs record `remote` as their Code runtime.

### Where it is wired in

- **Docker Compose:** `STUDIO_CODE_RUNTIME=remote STUDIO_SANDBOX_TOKEN=... docker compose --profile sandbox up`. The
  service runs on an internal network with no internet access, read-only, with all capabilities dropped except
  the few it needs to switch users.
- **Render:** [`deploy/render/render.full.yaml`](../../deploy/render/render.full.yaml) adds it as a private service
  with a generated token in its own environment group (the sandbox gets only that group).
- **Fly.io:** [`deploy/fly/sandbox.fly.toml`](../../deploy/fly/sandbox.fly.toml) is a second, private app reached at
  `http://<app>.internal:8080` (instructions in the file).
- **Anywhere else:** run the image as a private service (no public port) and set the variables above.

## Security model

What the service does for each call:

- Runs it in a new process with an **empty environment** and a temporary folder, in its own process group, killed
  at the time limit or when the run is cancelled.
- Drops it to **its own unprivileged uid** (61000 and up, one per concurrent call), so code cannot signal the
  service or read another call's files.
- Applies **rlimits** (address space, CPU seconds, open files, processes) and the `STUDIO_CODE_MEMORY` limit.
- **Python:** an audit hook, which the code cannot remove, refuses sockets, new processes (`subprocess`, `os.system`,
  `exec`, `fork`, `spawn`) and `ctypes`. **TypeScript:** Deno runs with no permissions, so no network, files,
  environment or processes, and only the cached packages.
- The service itself holds only the token, and its container has nothing of the studio in it except the Code
  runtime modules.

What it does **not** do, honestly:

- **It is process isolation, not container or VM isolation.** All calls share the sandbox container's kernel and
  file system (readable, not writable, by their uid). A kernel exploit or an escape from the Python audit hook
  (for example through a compiled extension) reaches the sandbox container, but not the studio's secrets or
  database, which are in other containers.
- **The Python network block is a guard inside the interpreter.** The real network boundary is the platform: on
  Docker Compose the sandbox has no route to the internet; on Render and Fly.io private services still have outbound
  internet access. If your platform offers egress rules, block outbound traffic from the sandbox.
- **The token is the only authentication.** Keep the service private (no public port) and rotate the token if it
  leaks (set the new value on both sides).
- It is weaker than the Docker runtime on your own server (one container per call, `--network none`), which stays
  the recommended choice where you can mount the Docker socket ([self-hosted guide](self-hosted.md)).

## Possible future backends

The runtime is a small interface in `backend/app/engine/code_runtime.py` (`CodeRunner`: `problem` and `exchange`),
so stronger backends can be added without touching the rest of the studio. Candidates are per-call microVMs such
as Fly Machines or Northflank sandboxes. They are not implemented.
