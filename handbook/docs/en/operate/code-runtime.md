# Code runtime

[Code mode](../guide/code-mode.md) lets admins write Python or TypeScript in Tool nodes.
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

## TypeScript

TypeScript nodes run on Deno in their own image, with the same isolation and
limits. Both languages are offered by default (`STUDIO_CODE_LANGUAGES`, for
example `python` to offer Python only).

```bash
docker build -t studio-code-ts:1 docker/studio-code-ts
```

| Variable | Default | Meaning |
| --- | --- | --- |
| `STUDIO_CODE_LANGUAGES` | `python,typescript` | Languages the editor offers |
| `STUDIO_CODE_TS_IMAGE` | `studio-code-ts:1` | The Deno image |
| `STUDIO_CODE_TS_PACKAGES` | `npm:zod@3,npm:date-fns@4` | The only packages code may import, each pinned as `name@major`; keep it equal to `docker/studio-code-ts/deps.ts` |
| `STUDIO_DENO` | `deno` on `PATH` | The Deno binary for subprocess mode |
| `STUDIO_CODE_TS_DENO_DIR` | empty | A Deno cache with the allowed packages, for subprocess mode |

Code must import a package with the same pinned major as the list, for
example `npm:zod@3` (or `npm:zod@3.25.1`, `npm:zod@3/mini`). An unversioned
`npm:zod` or another major is refused when you save, with `CODE_INVALID` and a
reason that names the allowed spec, because Deno would otherwise look for the
newest version, which the cache does not have.

In subprocess mode there is no image, so fill a cache with the same specs and
point the server at it (with no `STUDIO_CODE_TS_DENO_DIR` and no
`STUDIO_CODE_TS_PACKAGES`, no package is allowed):

```bash
export DENO_DIR=/var/lib/studio/deno-cache
printf 'import "npm:zod@3";\nimport "npm:date-fns@4";\n' > deps.ts
deno cache --no-config --no-lock deps.ts
export STUDIO_CODE_TS_DENO_DIR=$DENO_DIR STUDIO_CODE_TS_PACKAGES=npm:zod@3,npm:date-fns@4
```

Deno runs with no permission flag, `--no-remote` and `--cached-only`. Code
cannot read or write files, use the network, read environment variables or
start processes, even in subprocess mode, and it can import only packages
already in the image's cache. Memory is capped through the V8 heap
(three quarters of `STUDIO_CODE_MEMORY`). The admin card under **Settings →
Users** shows each language and whether it is ready.

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
- an alert in the Code config, and a **Runs on host** badge (with a tooltip) on the node and in
  the mode picker;
- `runtime: subprocess` on trace rows, plus one warning per run;
- a mark in run history (`code_runtime` on each run);
- the Code nodes card in **Settings → Users**;
- a `system.code_runtime_subprocess` audit entry on the first call after each
  start.

It never takes over by itself: with the default `docker` runtime and no
Docker, Code nodes fail validation. An unknown runtime value turns Code nodes
off.
