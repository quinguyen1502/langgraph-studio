# Decision Record

## Metadata

- Project: superstep
- Decision ID: DEC-0050
- Status: Accepted
- Owner: Thái Quí Nguyễn
- Created: 2026-10-23
- Updated: 2026-10-23
- Related Requirements: REQ-0046
- Related Architecture: DEC-0041 (Tool Code mode), DEC-0009 (layers), DEC-0008 (UI)
- Related Tasks: TASK-0081

## Context

REQ-0046 adds TypeScript to the Tool node Code mode (feasibility study, Option A: Deno; the owner approved P0-P2 on
2026-10-23). Let people with `code.write` pick Python or TypeScript in Code mode and see the state's type while writing TypeScript.

## Decision

1. `CodeEditor` (CodeMirror, python | typescript) replaces the Python-only editor; `PythonEditor` stays as a thin wrapper for the Code tab.
2. Language picker in Code mode (only languages the server offers); switching replaces only an untouched starter (edited code is kept, with a hint); TS starter from the server.
3. Generated `State` type from the workflow's state schema, shown above the editor and offered as `state.` completions.
4. Admin card: one row per language (image, packages, availability).
5. en/vi strings (parity test, glossary), handbook `guide/code-mode.md` en/vi.
6. vitest and an e2e TypeScript variant of the subprocess spec.

## Consequences

- DEC-0041 still holds: user code never runs in the server process; network is off; limits and error codes are shared.
- Out of scope (P3): type-check diagnostics, a LangGraph.js export, full TypeScript IntelliSense.
