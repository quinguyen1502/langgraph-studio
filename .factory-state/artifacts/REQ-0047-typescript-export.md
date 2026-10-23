# Requirement

## Metadata

- Project: superstep
- Requirement ID: REQ-0047
- Status: Implemented (TASK-0082 PR #112)
- Owner: Thái Quí Nguyễn
- Created: 2026-10-23
- Updated: 2026-10-23
- Source: owner request in chat, 2026-10-23, after approving the P2 panel fix: export a workflow as a runnable
  LangGraph.js TypeScript file next to the Python export. This brings the "LangGraph.js export" item of REQ-0046's P3
  into scope; the other P3 items (type-check diagnostics, full IntelliSense) stay out.

## Summary

- The Code tab can show and download the workflow as one LangGraph.js (`@langchain/langgraph`) TypeScript file, as it
  does for Python (REQ-0043). The two exporters share their language-neutral half and are picked from one registry.

## Acceptance Criteria

- A language choice (Python / TypeScript) in the Code tab, shadcn only, en/vi following the glossary, remembered.
- The export API takes `language` (`python` default, `typescript`) and keeps the common envelope; an unknown language
  is `EXPORT_LANGUAGE_UNSUPPORTED`, an imported repository is `TYPESCRIPT_EXPORT_UNAVAILABLE` (docs/api-errors.md).
- The state is an `Annotation.Root` with the same reducers (append, merge, add).
- TypeScript Code nodes are inlined as written; Python Code nodes become a stub that throws
  `not implemented in TS export` (mirroring the Python file's `NotImplementedError` for TypeScript nodes).
- LLM, Condition, Human, Join, For each, Decision, Subgraph, HTTP map to LangGraph.js / LangChain.js equivalents;
  the rest are clear stubs with a TODO.
- Credentials never appear in the file; settings and keys are read from environment variables.
- The generated file type-checks with `deno check` (npm: specifiers) and runs offline with the mock model.

## Out Of Scope

- Type-check diagnostics in the editor and full TypeScript IntelliSense (REQ-0046 P3).
- Porting registered Python tool functions to TypeScript.
