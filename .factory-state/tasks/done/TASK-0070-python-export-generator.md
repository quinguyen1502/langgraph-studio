# Task

## Metadata

- Project: superstep
- Task ID: TASK-0070
- Status: done (PR #93, REV-0064, QA-0064)
- Owner: Thái Quí Nguyễn
- Created: 2026-10-22
- Updated: 2026-10-22
- Requirement IDs: REQ-0043
- Design IDs: none (mapping set in REQ-0043)
- Architecture IDs: DEC-0009; new DEC-0045 (canvas → LangGraph code mapping)

## Objective

Generate one readable, runnable LangGraph Python file from a workflow version, serve it through the API, and prove in
the test suite that the file compiles and, with the mock model, takes the same path as the studio.

## Scope

### In Scope

- **Generator** `backend/app/engine/python_export.py`: a pure function `to_python(wf, name, version, children,
  example) -> str` (no I/O, no database):
  - header: workflow name, version, `pip install langgraph` (plus `httpx` and the LangChain provider package when
    needed), how to run, the environment variables for a real model, "credentials are not included";
  - `State(TypedDict, total=False)` with the field types; `append`, `merge`, `add` reducers written as small functions
    and used through `Annotated`; For each cursor fields;
  - a `render()` helper with the `{{ state.field }}` paths and filters of `engine/templating.py` (only when a node uses
    templating); `call_llm(prompt, model)`: the mock of `engine/llm.py` by default, `init_chat_model` when the
    environment selects a real provider; the Decision parsing of `engine/decisions.py`;
  - one function per node, every node type of REQ-0043's mapping table (Start / End as `START` / `END`, LLM,
    Condition router with `pick_branch`, Human with `interrupt` / `Command(resume=...)`, Decision, Join fan-in,
    For each loop, Subgraph as its own `build_<child>()` graph added as a node, Tool function / HTTP / Code, Retriever,
    MCP and Send email stubs with a `TODO`, Notes as comments);
  - `build_graph()` with `add_node` (with `RetryPolicy` / `CachePolicy` when set), edges, conditional edges and
    `compile(checkpointer=MemorySaver())`; node timeouts as a comment;
  - `__main__`: runs the example input, prints each step (`stream`), resumes Human interrupts with example answers.
  - English comments that explain each LangGraph idea once (owner, Q2).
- **Names.** Function names from labels: slugged (diacritics removed), valid identifiers, not keywords, unique; the
  original label and node id in a comment. String literals safe for quotes, backslashes and braces.
- **No secrets.** Credentials, keys, SMTP, MCP server settings, approvers, escalation addresses and channel ids are
  never written; credential references become a comment naming the environment variable.
- **Deterministic.** Same input, same bytes (sorted where the graph has no order; no timestamps).
- **Service and API.** `WorkflowService` (or a small `ExportService`) loads the version (latest when none), checks
  view access, loads subgraph children the user may read (same rules and depth limit as a run), takes the example
  input from the first test case (or empty Start fields) and its Human answers. Route
  `GET /api/workflows/{wid}/export/python?version=N` returns `text/x-python` with
  `Content-Disposition: attachment; filename="<slug>.py"`. Imported repositories are refused. Errors in the shared
  envelope; new codes (if any) in `CATALOG`, `docs/api-errors.md` and both locales.
- **DEC-0045** records the mapping and the choices (runnable with mock, English comments, subgraphs as graphs,
  stubs for studio services, timeouts as comments).
- **Tests** `backend/tests/test_python_export.py`:
  - every built-in template and fixture graphs (parallel branches, join, For each, subgraph, reducers, retry and cache,
    HTTP and Code tools, odd labels): the file passes `py_compile` and `pyflakes`-style unused-import check (or `ast`
    check), and run in a subprocess with the mock it visits the same nodes in the same order as the studio's mock run
    (Start / End excluded), Human answers from the template's test cases;
  - no credential value, id or approver address in the output;
  - byte-identical twice; one prompt change → one changed line;
  - API: view permission, version, download name, imported repository refused.

### Out Of Scope

- The editor panel (TASK-0071) and the handbook page (TASK-0072).
- Working Retriever, MCP and Send email code; importing the file back; multi-file projects.

## Inputs

- REQ-0043 (mapping table, edge cases, Q1–Q3 answers).
- `backend/app/engine/compiler.py`, `nodes.py`, `decisions.py`, `foreach.py`, `emails.py`, `reducers.py`,
  `node_policy.py`, `templating.py`, `llm.py` (`mock_llm`), `tools.py`, `subgraphs.py`, `validator.py`.
- `backend/app/services/workflow_service.py` (versions, access), `workflow_test_service.py` (example input),
  `engine/templates.py` (`TESTS`).

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0043-python-export.md`
- Design: none
- Architecture: `docs/backend-architecture.md` (DEC-0009)
- Decisions: DEC-0045 (to write), DEC-0013 (studio Human pauses), DEC-0038 (For each)
- Discovery: the compiler builds the `StateGraph` with studio wrappers (ledger, ports, policies); the export writes the
  plain LangGraph equivalent.
- Clarifications: none

## Expected Outputs

- `engine/python_export.py`, service method, API route, error codes if any
- DEC-0045
- `tests/test_python_export.py`
- Handbook API reference (en, vi) entry for the route

## Implementation Notes

- Build the file from small string pieces per node type; keep the mapping in one table-like place so TASK-0072's docs
  table matches it.
- The path comparison runs the generated file with the same `langgraph` installed in the backend venv; read the visited
  nodes from the `stream(..., stream_mode="updates")` output printed by `__main__` (or a `--trace` flag) and compare
  with the studio run's node events.
- The mock in the file must give the same answers as `mock_llm` for the paths to match; copy its rules, and a test
  guards that both stay in step.

## Constraints

- Layers (DEC-0009): engine without I/O; service for loading and access; router returns the text. No schema change.
- The generated file imports nothing from Superstep; depends on `langgraph` (and `httpx`, a LangChain provider package
  only when used).
- SQLite and Postgres.

## Dependencies

- None.

## Acceptance Criteria

- Every built-in template and fixture graph exports a file that compiles and, with the mock, visits the same nodes in
  the same order as the studio's mock run.
- Each node type is exported as REQ-0043's mapping table says; subgraphs are separate graphs added as nodes.
- No secret appears in the output; output is byte-identical for the same version; a one-prompt change is a one-line
  diff.
- The API serves the file with view permission and a download filename, refuses imported repositories, and uses the
  shared envelope for errors.
- pytest (SQLite and Postgres) and `tests/test_layers.py` pass.

## Validation Plan

- `pytest tests/test_python_export.py` and the full suite; Postgres in CI.
- Manually read two exported files (Router, Leave request) for readability.

## Assumptions

- The backend's `langgraph` version supports `interrupt`, `Command`, `MemorySaver`, `RetryPolicy` and `CachePolicy`
  as used by the compiler today.

## Open Questions

- None.

## Activity Log

- 2026-10-22: planned from REQ-0043.
- 2026-10-22: started after PR #92 merged (owner approved the plan).
- 2026-10-22: implemented; DEC-0045 written. Review REV-0064 (fixed: graph values written into the code unchecked),
  QA QA-0064.
- 2026-10-22: CI green on PR #93 (Postgres included); the owner approved the merge.

## Handoff Notes

- TASK-0071: `GET /api/workflows/{wid}/python[?version=n]` returns `{filename, version, code, nodes}`; `nodes` maps a
  top-level node id to 1-based `[first, last]` line ranges, the first one its function (Start and End: their edges;
  a Note: its comment). Imported repositories get `PYTHON_EXPORT_UNAVAILABLE`.
- A change to `mock_llm`, `pick_branch`, `templating` or the Jev mock needs the same change in the generator's
  helpers (`test_helpers_match_the_engine` fails otherwise).
