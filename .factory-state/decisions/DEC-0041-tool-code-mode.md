# Decision Record

## Metadata

- Project: langgraph-studio
- Decision ID: DEC-0041
- Status: Proposed
- Owner: Thái Quí Nguyễn
- Created: 2026-10-19
- Updated: 2026-10-19
- Related Requirements: REQ-0039 (CLAR-0001)
- Related Architecture: DEC-0009 (layers), DEC-0023 (roles and permissions), REQ-0009 / TASK-0015 (Docker sandbox), DEC-0008 (UI)
- Related Tasks: TASK-0053, TASK-0054, TASK-0055, TASK-0056

## Context

REQ-0039 adds a Tool node mode `code`: user-written Python that runs once per call. The owner settled these points in CLAR-0001:
- who may write code: the `code.write` permission;
- network: always off;
- packages: a fixed image;
- credentials: none;
- without Docker: an explicit host subprocess mode with visible warnings.

The TASK-0015 sandbox (`engine/sandbox/container.py`) already builds a locked-down `docker run` and kills it on timeout. The engine may import `core` but not `services`.

## Decision

1. **One runtime interface in `engine/code_runtime.py`.**
   - `run_code(source, state, limits) -> CodeResult`, where `CodeResult` holds `value`, `stdout`, `runtime` and `duration_ms`.
   - It picks a backend from `core/config`:
     - `code_runtime()` returns `docker`, `subprocess` or `off`;
     - `STUDIO_ENABLE_CODE_NODES` unset gives `off`;
     - `STUDIO_CODE_RUNTIME` chooses `docker` (default) or `subprocess`;
     - there is no automatic fallback.
   - Both backends speak the same protocol with the same in-process runner script, `engine/sandbox/code_runner.py`:
     - input on stdin: one JSON object `{source, state}`;
     - output on stdout: one JSON line, either `{ok: true, value, stdout}` or `{ok: false, error, traceback, stdout}`.
2. **Docker backend.**
   - It reuses `container.build`, `captured` and `failure_event`, with `--network none`, `--read-only`, `--cap-drop ALL`, `no-new-privileges`, a 64 MB `/tmp` tmpfs, and memory, CPU and pids limits.
   - It mounts no host directory except the runner (read-only), and gets an empty environment.
   - The image is `STUDIO_CODE_IMAGE`, default `studio-code:1`, built from `docker/studio-code/Dockerfile`: `python:3.12-slim` plus `pydantic` and `python-dateutil`, with pinned versions.
   - Limits come from `STUDIO_CODE_MEMORY`, `STUDIO_CODE_CPUS` and `STUDIO_CODE_PIDS`.
   - The time limit is the node's timeout (REQ-0019), capped by `STUDIO_CODE_MAX_SECONDS` (default 30).
3. **Subprocess backend.**
   - It runs `sys.executable -I` on the runner, with an empty environment and a fresh temporary working directory, in a new session so that a timeout kills the whole process group.
   - On Linux, rlimits are set in `preexec_fn`: `RLIMIT_AS`, `RLIMIT_CPU`, `RLIMIT_NOFILE` and `RLIMIT_NPROC`.
   - It is never isolation, and every surface labels it (decision 6).
4. **Node and validation.**
   - `nodes.py` calls `run_code` for `mode == "code"` and writes `value` to `output_field`.
   - The `CodeResult` is attached to the node's trace event, which gets `stdout` (truncated) and `runtime` fields.
   - The validator checks that:
     - the source is non-empty and at most 64 KB;
     - it compiles with `compile()` and is never executed;
     - it defines a top-level `def main(state)`;
     - `code_runtime() != "off"`;
     - Docker can be reached when the runtime is `docker`.
   - Size limits: state in 1 MB, result 1 MB, stdout 64 KB (truncated with a marker).
   - Code is a normal runtime-policy type: retry, timeout and cache apply, because the network is off and code has no outside effects.
   - Code is not in `SIDE_EFFECT_TYPES`.
5. **Permission `code.write`** in `core/permissions.py`:
   - it is in `PERMISSIONS["admin"]` only;
   - it is listed in the admin role matrix.
   - One service helper, `services/access.py: require_code_write(old_graph, new_graph, user)`, compares the Code nodes' `code` per node id. It raises `CODE_WRITE_FORBIDDEN` (403) when a user without the permission adds a Code node or changes its source.
   - Moving, renaming, deleting a node, or changing the output field stays allowed.
   - Every path that writes a graph calls the helper:
     - workflow save and create;
     - duplicate (allowed, since the source does not change);
     - import;
     - template use and template import;
     - version restore.
6. **Runtime visibility.**
   - `GET /api/meta/runtime` returns:
     ```
     {code_runtime, image, limits, packages}
     ```
     The frontend reads it once through `lib/api.ts`; `packages` comes from `STUDIO_CODE_PACKAGES`, or a constant matching the default image.
   - With `subprocess`:
     - one `WARNING` log at start-up;
     - the editor Alert (`--warning`) in the config;
     - a canvas badge;
     - a "Not isolated" badge in the mode picker;
     - `runtime: subprocess` on trace rows;
     - one run-panel warning per run;
     - a `code_runtime` column on runs (Alembic migration), so history keeps it;
     - an admin Settings card;
     - an audit entry `system.code_runtime_subprocess` on the first Code call after each server start.
7. **Test with sample state.**
   - `POST /api/workflows/{id}/nodes/{node_id}/test-code` with body `{state}` runs the node's saved or unsaved source (sent in the body) through the same `run_code`.
   - It needs run access and `code.write`, writes no run, and is rate-limited per user.

## Rationale

- One runner script and one result shape keep the two backends from drifting.
- The tests for one backend cover the protocol of the other.
- A per-call container is simple and matches TASK-0015. A warm pool can come later without changing the interface.
- Checking the permission by diffing code per node id lets people without `code.write` keep using and arranging workflows that contain code.

## Alternatives Considered

- In-process `exec` with a restricted namespace. Not chosen: it is not a real sandbox in CPython.
- RestrictedPython. Not chosen: it limits the language without protecting the host, and adds a dependency.
- A long-lived worker container. Not chosen for the first version: state can leak between calls, and lifecycle handling gets harder.

## Consequences

- Running a Code node needs Docker on the API and worker hosts, or the explicit subprocess flag.
- The Compose setup documents mounting the Docker socket for the worker, as imports already do.
- A first call on a cold image is slow, so the README tells admins to pre-pull or build `studio-code:1`.
