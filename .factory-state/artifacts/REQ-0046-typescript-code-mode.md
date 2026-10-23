# Requirement

## Metadata

- Project: superstep
- Requirement ID: REQ-0046
- Status: Implemented (P0 TASK-0079 PR #109, P1 TASK-0080 PR #110, P2 TASK-0081 PR #111)
- Owner: Thái Quí Nguyễn
- Created: 2026-10-23
- Updated: 2026-10-23
- Source: owner question in chat, 2026-10-23: "Look at the Code part, can we bring TypeScript in?". The feasibility
  study (Option A: Deno) was approved with phases P0, P1 and P2; P3 is out of scope.

## Summary

- A Tool node in Code mode can be written in Python or TypeScript. TypeScript runs on Deno with the same contract as
  Python: `main(state)` gets a JSON copy of the state, its return value goes to the output field, printed output goes
  to the trace, network is off and the same time, memory, CPU and process limits apply.

## Acceptance Criteria

- Existing graphs (no `language`) keep running as Python, with no migration.
- `STUDIO_CODE_LANGUAGES` picks the offered languages; an unknown or disabled one gives `CODE_LANGUAGE_UNSUPPORTED`.
- Docker runtime: TypeScript runs in `studio-code-ts:1` with the same `docker run` locks as Python.
- Subprocess runtime: Deno runs with no permission at all (no file, network, env, run, ffi or sys access).
- Imports: only `npm:` / `jsr:` packages in the allowlist (`STUDIO_CODE_TS_PACKAGES`, pre-cached in the image).
- Changing a node's language needs `code.write`, like changing its code.
- The editor offers a language picker, a TypeScript starter and a `State` type generated from the state schema;
  the admin card shows each language; en/vi and the handbook explain it.

## Out Of Scope

- Type-check diagnostics (`deno check`), a LangGraph.js export of the workflow, full TypeScript IntelliSense (P3).
