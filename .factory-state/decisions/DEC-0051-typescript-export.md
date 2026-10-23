# Decision Record

## Metadata

- Project: superstep
- Decision ID: DEC-0051
- Status: Accepted
- Owner: Thái Quí Nguyễn
- Created: 2026-10-23
- Updated: 2026-10-23
- Related Requirements: REQ-0047, REQ-0046, REQ-0043
- Related Architecture: DEC-0045 (Python export), DEC-0049 (TypeScript on Deno), DEC-0009 (layers)
- Related Tasks: TASK-0082

## Context

The Python export (DEC-0045) writes a graph as LangGraph Python. TypeScript Code nodes (DEC-0049) cannot run in it.
The owner asked for a LangGraph.js export that mirrors the Python one without copy-paste.

## Decision

1. One base, two writers: `export_common.GraphWriter` holds everything that does not depend on the language; each
   exporter only writes syntax. `exporters.EXPORTERS` maps `language` to `(label, media type, write)`; the service
   and the API pick from it, so a third language is one module and one registry entry.
2. Target: Deno first. Imports are pinned `npm:` specifiers (`@langchain/langgraph@^1.5`,
   `@langchain/langgraph-checkpoint@^1`, `langchain@^1` loaded only when `LLM_PROVIDER` is set). TypeScript Code nodes
   already use `npm:` imports, so the file runs and type-checks as is; Node needs the prefixes dropped (documented).
3. State: `Annotation.Root`; `append` / `merge` / `add` reducers with defaults `[]`, `{}`, `0` (the values Python's
   `Annotated[list, ...]` starts from). Updates go through `asUpdate()` because canvas values are typed at run time.
4. TypeScript Code nodes are inlined in an IIFE (`export` dropped, imports hoisted and de-duplicated); Python Code
   nodes and registered Python tool functions are stubs that throw `not implemented in TS export`.
5. Retriever, MCP and Send email stubs mirror the Python file; HTTP uses `fetch` with `redirect: "manual"`. LangGraph.js
   has a node `timeout`, so the canvas timeout maps to it (the Python file can only comment).
6. Nodes not reachable from Start are left out with a comment: LangGraph.js `compile()` rejects them.
7. Settings and keys come from environment variables through `env()`, which works on Deno and Node; `sanitize` keeps
   credentials out of both files.
8. API: `language` query on the JSON endpoints and a `{language}` path on the file endpoint (old URLs unchanged).

## Consequences

- `python_export` output is unchanged (its tests pass unmodified). Builtin templates without Python tool functions
  take the studio's mock path to the same final state in both languages (tests run them under Deno).
- Mock text matches the studio because `pyJson()` writes JSON as Python does.
- The `deno check` tests need the npm registry once; offline they skip.
