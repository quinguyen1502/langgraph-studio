# Requirement

## Metadata

- Project: langgraph-studio
- Requirement ID: REQ-0039
- Status: Proposed
- Owner: Thái Quí Nguyễn
- Created: 2026-10-19
- Updated: 2026-10-19
- Source: owner question "Vậy có thể thêm 1 mode cho việc tự write và execute code trên node ko?" (2026-10-19), after the explanation of the Tool node's Python function mode

## Summary

A third mode for the Tool node, **Code**, next to `function` and `http`. The user writes a short Python function in the node, and each run executes it in an isolated container. It gets the run state and returns a value that goes into the node's output field.

## Problem Or Opportunity

- **Function mode** only offers functions registered on the server with `@register_tool` (`backend/app/engine/tools.py`). New logic needs a code change and a deploy.
- **HTTP and MCP** need a service someone else hosts.
- Small transformations have no home in the canvas: parse a string, reshape a JSON object, compute a score, pick fields. They push users to stand up a service or ask for a server change.

## Scope

### In Scope

- `mode: "code"` on the Tool node:
  - `data.code` holds the source; the entry point is `def main(state): ...`;
  - the return value is written to `output_field`.
- Execution in the Docker sandbox from TASK-0015 (`backend/app/engine/sandbox/container.py`):
  - a fresh container per call;
  - read-only root, `--cap-drop ALL`, `no-new-privileges`;
  - limits on memory, CPU and pids, and a wall-clock time limit;
  - an empty environment that never holds server secrets.
- A small in-container runner:
  - reads the state as JSON on stdin and calls `main(state)`;
  - writes one JSON result to stdout;
  - captures `print()` output and the traceback.
- The trace shows each call's result, captured stdout (truncated) and, on failure, the traceback as the node error.
- Editor: a Python code field with syntax highlighting, a starter template, and **Test with sample state**, which runs the code once against the run panel's input and shows the result or the error.
- Validation before a run:
  - the code is not empty;
  - it compiles (`compile()` only; nothing is executed on the server);
  - it defines `main`;
  - the mode is allowed for the editing user (see Open Questions).
- en and vi strings. New error codes go in `core/errors.py` CATALOG, `docs/api-errors.md` and both locales.
- README (en and vi): what the mode is for, its limits, and how to enable it.

### Out Of Scope

- Languages other than Python.
- Changing the existing `function` mode or the `@register_tool` registry.
- Installing packages per node at run time (unless the owner picks that option; see Open Questions).
- Keeping state between calls: no shared filesystem and no warm interpreter between runs.
- A full IDE: no debugger, breakpoints or language server.

## Stakeholders Or Users

- Workflow authors (editor role, possibly admin only; see Open Questions).
- Project owner or administrator, who enables the feature and sets limits.
- Viewers and other users who run a shared workflow containing a Code node.

## Current Context

- Tool node runtime: `backend/app/engine/nodes.py` (`t == "tool"`, modes `http` and the default `function`).
- Validator: `backend/app/engine/validator.py` (Tool node checks).
- Sandbox: TASK-0015 / REQ-0009, `container.build`, `captured`, `sandbox_env`, `allow_secret`. The flags are `STUDIO_IMPORT_*` (image, memory, CPUs, pids, network, host dir).
- Node settings: REQ-0019 (retry, wait, timeout, cache TTL per working node).
- Idempotency keys for side effects: TASK-0021 (`engine/effects.py`).
- Roles and permissions: `backend/app/core/permissions.py` (DEC-0023):
  - roles: admin, editor, viewer;
  - workflow access: owner, editor or viewer share.
- Runs execute in the API process or the worker (`services/run_worker.py`). Both need Docker for this mode.
- Templates: save-as-template strips secrets (TASK-0028); the code would travel with templates, exports and imports.
- Outbound HTTP elsewhere goes through the SSRF guard (`core/net.py`, REQ-0027). Traffic from inside the container would not.

## Desired Behavior

- In the Tool node config the user picks **Code**, writes `main(state)` and picks an output field.
- A run reaching the node starts a sandbox container:
  - it passes the state and waits for at most the node timeout (or a server default);
  - the returned value is stored in the output field;
  - the run continues.
- Failures stop the node with a clear error and the run follows the node's retry settings: an exception in user code, a non-JSON return value, the time limit, the memory limit, or Docker unavailable.
- The run panel and trace show the result, the captured `print()` output (truncated) and the traceback.
- **Test with sample state** gives the same result as a real run for the same state, and writes no run history.

## Business Rules

- User code never runs in the API or worker process.
- The container never receives server environment variables, DB access or the credential store unless the owner allows credentials (see Open Questions). Even then it gets only what the node lists.
- The state passed in is a JSON copy; the code cannot change the run except through its return value.
- Size limits: state in, result out, and stdout (for example 1 MB result and 64 KB stdout; final values set in the task).
- Who may add or change a Code node is checked on save, on import and on template use, not only in the UI.
- A workflow shared with a viewer can still be run by that viewer. The code runs with the sandbox's rights, never the viewer's or the owner's.

## Constraints

- Docker is the only isolation runtime (REQ-0009 decision). gVisor and Firecracker stay out of scope.
- Mock or offline mode must keep working. A workflow without Code nodes must not need Docker.
- Layers per DEC-0009:
  - the runner and the container call live in `engine/`;
  - the permission check lives in `services/`;
  - schema changes, if any, go through Alembic.
- UI: shadcn components and theme tokens only (DEC-0008). The code editor component must follow the theme in light and dark.

## Acceptance Criteria

- A Code node returning `state["message"].upper()` writes the upper-cased message to its output field, and the next node can use it.
- `print()` output and a raised exception appear in the trace. The run fails with the traceback, and retry settings apply.
- An endless loop is stopped at the time limit; allocating past the memory limit is stopped. Both are reported as node errors.
- Code cannot read server environment variables (for example `JWT_SECRET`) or files outside the container, and cannot reach the network unless the owner allows it.
- Saving or importing a workflow with a Code node is refused for users not allowed to write code, with an error code shown in en and vi.
- Without Docker, a Code node fails validation with a clear message, and other workflows run as before.
- pytest covers runner I/O, limits, isolation and permissions (Docker-dependent tests skip when Docker is missing). Playwright covers editing, Test with sample state, and a run.

## Edge Cases

- `main` missing, wrong signature, or a syntax error: shown at validation, before the run starts.
- A return value that is not JSON-serialisable (a set, a datetime, a custom object): node error naming the type.
- Very large state or result: refused with a size error, not truncated silently.
- Cancelling a run while the container is running: the container is killed (the same path as imports).
- Many parallel Code nodes, for example inside For each: container start-up cost and a cap on concurrent containers.
- Loop iterations call the code each time; the trace shows each call as its own row.
- A Code node in a template or export: the code is kept, and the permission rule applies when it is used or imported.

## Assumptions

- A new container per call is acceptable, at about 0.5–1.5 s overhead per call on a warm image. A warm pool is a later optimisation if needed.
- The container uses its own image setting (for example `STUDIO_CODE_IMAGE`, default `python:3.12-slim`), separate from the import image.
- The feature is off by default behind a flag (for example `STUDIO_ENABLE_CODE_NODES`), like repo import.

## Open Questions

Owner decisions are collected in `.factory-state/artifacts/CLAR-0001-tool-code-mode.md`, answered with `factory clarify CLAR-0001`:

1. **Who may write code:** admins only, users with a new `code.write` permission, or every editor?
2. **Network access:** always off, off by default with a per-node switch, or always on?
3. **Python packages:** standard library only, a fixed image with chosen packages, or per-node requirements installed at run time?
4. **Credentials:** none in the first version, or chosen credentials passed to the code (as env vars or as an argument)?
5. **Without Docker:** turn the mode off, or allow a host subprocess behind an explicit flag (less safe)?

## Related Artifacts

- `.factory-state/artifacts/CLAR-0001-tool-code-mode.md`
- `.factory-state/artifacts/REQ-0009-sandboxed-imports.md`
- `.factory-state/artifacts/REV-0029-task-0015-container-sandbox.md`
- `.factory-state/artifacts/REQ-0019-node-execution-settings.md`
- `.factory-state/artifacts/REQ-0027-review-hardening.md` (SSRF guard)
- `backend/app/engine/tools.py`, `backend/app/engine/nodes.py`, `backend/app/engine/sandbox/container.py`, `backend/app/core/permissions.py`
