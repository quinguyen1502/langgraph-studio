# Code runtime

[Code mode](../guide/code-mode.md) lets admins write Python in Tool nodes.
This page is the server side: how to turn it on and what isolates it.

## Turn it on

```bash
docker build -t studio-code:1 docker/studio-code
export STUDIO_ENABLE_CODE_NODES=1
```

The image is `python:3.12-slim` with `pydantic` and `python-dateutil`.
`STUDIO_CODE_IMAGE` picks another image; list its packages in
`STUDIO_CODE_PACKAGES` (comma-separated) so the editor shows them. While the mode is off, or
Docker or the image is missing, a workflow with a Code node fails validation
and says why. `GET /api/meta/runtime` reports what the editor sees.

Under Compose the API and the worker start the containers through the Docker
socket, like repo import.

## Isolation

Every call gets a new container:

| Control | Setting |
| --- | --- |
| Network | `--network none` |
| Filesystem | Read-only root, a 64 MB tmpfs `/tmp`, no host mounts |
| Privileges | `--cap-drop ALL`, `no-new-privileges`, the API's own uid and gid |
| Environment | `HOME=/tmp` and two Python flags; no server variable or credential |
| Input | A JSON copy of the state on stdin |

## Limits

| Variable | Default | Meaning |
| --- | --- | --- |
| `STUDIO_CODE_MEMORY` | `256m` | Memory (swap equal to memory) |
| `STUDIO_CODE_CPUS` | `0.5` | CPU share |
| `STUDIO_CODE_PIDS` | `64` | Processes |
| `STUDIO_CODE_MAX_SECONDS` | `30` | Cap on the node's timeout |
| `STUDIO_CODE_CONCURRENCY` | `4` | Containers at once per server process |
| `STUDIO_CODE_TEST_PER_MINUTE` | `20` | Editor test calls per user per minute |

A cancelled run kills its container.

## Without Docker

`STUDIO_CODE_RUNTIME=subprocess` runs the code as a child process of the
server, with an empty environment and its own temporary folder. On Linux it
also gets limits on memory, CPU time, open files and processes; the time limit
kills the whole process group.

!!! danger "This is not a sandbox"
    In subprocess mode the code can use the network and read any file the
    server user can read, including the database file and `secret.key` of a
    SQLite setup. On macOS the memory limit does not apply. Use it only for
    trusted local work.

The studio makes it visible everywhere:

- a start-up `WARNING` in the log;
- `code_runtime: "subprocess"` in `GET /api/meta/runtime`;
- an alert in the Code config, and a **Not isolated** badge on the node and in
  the mode picker;
- `runtime: subprocess` on trace rows, plus one warning per run;
- a mark in run history (`code_runtime` on each run);
- the Code nodes card in **Settings → Users**;
- a `system.code_runtime_subprocess` audit entry on the first call after each
  start.

It never takes over by itself: with the default `docker` runtime and no
Docker, Code nodes fail validation. An unknown runtime value turns Code nodes
off.
