# Decision Record

## Metadata

- Project: superstep
- Decision ID: DEC-0048
- Status: Accepted
- Owner: Thái Quí Nguyễn
- Created: 2026-10-23
- Updated: 2026-10-23
- Related Requirements: REQ-0046
- Related Architecture: DEC-0041 (Tool Code mode), DEC-0009 (layers), DEC-0008 (UI)
- Related Tasks: TASK-0079

## Context

REQ-0046 adds TypeScript to the Tool node Code mode (feasibility study, Option A: Deno; the owner approved P0-P2 on
2026-10-23). Make the Tool node Code mode language-pluggable without changing what Python users see, so TypeScript (TASK-0080) is one new strategy.

## Decision

1. `engine/code_languages.py`: `CodeLanguage` interface (problems, command, host_command, host_env, image, packages, host_problem, starter), `Python` strategy, `LANGUAGES`, `language_of`, `enabled`, `get`.
2. `code_runtime.run_code/problems/unavailable/runtime_error` take a `language` (default Python); everything shared (payload, limits, kill, result parsing, error codes) stays in one place.
3. `data.language` on Code-mode Tool nodes; missing = `python` (no migration).
4. `STUDIO_CODE_LANGUAGES` (default `python`).
5. `CODE_LANGUAGE_UNSUPPORTED` (400) in `core/errors.py`, `docs/api-errors.md`, en/vi locales.
6. `code.write`: switching a node's language counts as writing code (`permissions.code_sources`).
7. Validator checks per language; `/api/meta/runtime` adds `languages[]`; `/api/code/test` takes `language`.
8. Python export writes a `NotImplementedError` stub for a non-Python Code node.

## Consequences

- DEC-0041 still holds: user code never runs in the server process; network is off; limits and error codes are shared.
- Out of scope (P3): type-check diagnostics, a LangGraph.js export, full TypeScript IntelliSense.
