# Decision Record

## Metadata

- Project: superstep
- Decision ID: DEC-0049
- Status: Accepted
- Owner: Thái Quí Nguyễn
- Created: 2026-10-23
- Updated: 2026-10-23
- Related Requirements: REQ-0046
- Related Architecture: DEC-0041 (Tool Code mode), DEC-0009 (layers), DEC-0008 (UI)
- Related Tasks: TASK-0080

## Context

REQ-0046 adds TypeScript to the Tool node Code mode (feasibility study, Option A: Deno; the owner approved P0-P2 on
2026-10-23). Run `export function main(state)` written in TypeScript with the same contract, limits and error codes as Python.

## Decision

1. `engine/sandbox/code_runner.ts` (Deno, std only): stdin `{source, state, stdout_max}`, one JSON result line, console capture, `<code>` frames only, `not_json` for undefined/BigInt/functions/cycles, sync or async `main`.
2. `TypeScript` strategy in `code_languages.py`: static check (export main, import allowlist), `deno run --no-prompt` with no `--allow-*` flag, V8 heap cap from `STUDIO_CODE_MEMORY`, `--no-remote`, `--cached-only`, `--no-config`, own `DENO_DIR` per call on the host.
3. Config: `STUDIO_CODE_LANGUAGES` default `python,typescript`, `STUDIO_CODE_TS_IMAGE` (`studio-code-ts:1`), `STUDIO_CODE_TS_PACKAGES`, `STUDIO_DENO` (binary for the subprocess runtime).
4. `docker/studio-code-ts/Dockerfile` (denoland/deno, pre-cached allowlisted npm packages, non-root, no network at run time); compose env.
5. Backend tests for both languages (subprocess runtime with a real Deno).

## Security Notes

- The Docker runtime uses the same locks as Python: `--network none`, a read-only root, `--cap-drop ALL`,
  `no-new-privileges`, memory equal to swap, a CPU and process limit, a non-root uid and no mounts.
- Deno gets **no** `--allow-*` flag and `--no-prompt`, so file, network, environment, `run`, `ffi` and `sys` access
  fail with `NotCapable` (`CODE_FAILED`) on both runtimes.
- `--no-remote` and `--cached-only` mean only packages already in Deno's cache can load. The static allowlist check
  (`STUDIO_CODE_TS_PACKAGES`) rejects other literal imports with `CODE_INVALID` before anything runs. A computed
  `import(x)` is not seen by the check, but it still cannot load anything uncached.
- On the host runtime:
  - Memory is limited by the V8 heap cap (`--max-old-space-size` = 75 % of `STUDIO_CODE_MEMORY`), not by
    `RLIMIT_AS`, because V8 reserves far more address space than it uses.
  - `RLIMIT_NPROC` is not set: it counts every process of the server user, and Deno cannot start processes anyway.
  - `RLIMIT_CPU` and `RLIMIT_NOFILE` are still set.
  - The runtime stays labelled "not isolated": there is no cgroup, and it shares the kernel with the server.
- A V8 out-of-memory abort (exit 133 / SIGTRAP) is `CODE_MEMORY`, like 137 for Python.

## Consequences

- DEC-0041 still holds: user code never runs in the server process; network is off; limits and error codes are shared.
- Out of scope (P3): type-check diagnostics, a LangGraph.js export, full TypeScript IntelliSense.
