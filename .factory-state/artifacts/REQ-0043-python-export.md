# Requirement

## Metadata

- Project: superstep
- Requirement ID: REQ-0043
- Status: Implemented (TASK-0070 PR #93, TASK-0071 PR #94, TASK-0072 PR #96)
- Owner: Thái Quí Nguyễn
- Created: 2026-10-22
- Updated: 2026-10-22 (the editor entry is named "Code" / "View as code": other languages, e.g. TypeScript, may
  follow; owner, during TASK-0071)
- Source: owner request in chat, 2026-10-22. After REQ-0042 (proposal 3), the owner asked for proposal 5. It serves
  the learning goal: export a workflow as a readable LangGraph Python file that matches the graph on the canvas, so a
  learner sees how the graph is written in code. Proposal 6 (channels as run triggers) stays for later.

## Summary

- **View as Python** in the editor shows the workflow as one readable LangGraph Python file, next to the canvas:
  the state as a `TypedDict`, one function per node, and the `StateGraph` built with `add_node`, `add_edge` and
  `add_conditional_edges`, then compiled.
- Selecting a node on the canvas highlights its function and its edges in the code.
- **Copy** and **Download .py**. The file runs on its own with `pip install langgraph`: offline with a mock model by
  default, or with a real model when the learner sets an API key.
- Comments explain the LangGraph idea behind each part (state and reducers, `START` / `END`, conditional edges,
  `interrupt` for Human nodes, the checkpointer, subgraphs).

## Problem Or Opportunity

- The vision names "Learning aid for LangGraph concepts" as a goal. Today a learner builds a graph on the canvas but
  never sees the LangGraph code behind it; the compiler (`engine/compiler.py`) builds the `StateGraph` in memory, mixed
  with studio concerns (trace, ledger, ports, policy checks), which is not code to learn from.
- Repository import (REQ-0001, REQ-0009) goes from code to canvas. There is no way from canvas to code, so a learner cannot
  carry a prototype into their own project.

## Scope

### In Scope

- **Generator** (backend engine, pure function of the workflow JSON): one `.py` file per workflow version, the same
  output for the same graph (stable order, no timestamps), so two versions diff cleanly.
- **What the file contains:**
  - a header: the workflow name, version, how to install and run, and that credentials are not included;
  - `State` as a `TypedDict` with the field types; reducer fields as `Annotated[...]` with the reducer function
    (`append`, `merge`, `add` written out, `replace` as a plain field);
  - one function per node, named after its label (unique, valid Python names), with the node id in a comment;
  - `build_graph()`: `StateGraph(State)`, `add_node`, `add_edge`, `add_conditional_edges` with a router function and a
    path map, fan-out edges, fan-in (`add_edge([...], join)`), `RetryPolicy` / `CachePolicy` where the node sets them,
    `compile(checkpointer=MemorySaver())`;
  - a `__main__` block that runs the graph with an example input (the first test case's input when there is one, else
    the Start fields with empty values), prints each step, and shows how to resume a Human node with
    `Command(resume=...)`.
- **Node mapping** (each one explained in a comment):

  | Canvas | Code |
  | --- | --- |
  | Start / End | `START` / `END` edges |
  | LLM | renders the prompt from state, calls `call_llm(prompt, model)` |
  | Condition | router function returning a label, `add_conditional_edges` with the label → node map and the default |
  | Human | `interrupt(prompt)` (LangGraph's own pause), resumed with `Command(resume=answer)` |
  | Decision | `call_llm` asking for one label or a score, then the same parsing as the studio |
  | Join | fan-in edge from every incoming branch |
  | For each | the studio's loop: a cursor field, an `each` / `done` router |
  | Subgraph | the child workflow as its own `build_<child>()` graph, added as a node (LangGraph subgraph idiom) |
  | Tool: built-in function | the function's code, copied in |
  | Tool: HTTP | an `httpx` request built from the node's method, URL and body |
  | Tool: Code | the node's `main(state)` code, as written |
  | Retriever, MCP, Send email | a stub function with a `TODO` that says what the studio does there; the mock returns an empty or sample value so the graph still runs |
  | Note | a comment above the nodes it sits next to |

- **Templating.** `{{ state.field }}` references, paths and filters become a small `render()` helper in the file,
  with the same behaviour as `engine/templating.py`.
- **Models.** `call_llm` uses the mock (same rules as `engine/llm.py` `mock_llm`) unless an environment variable names
  a real provider and key; then it uses LangChain's `init_chat_model` with the node's model name. The header lists the
  extra `pip install` for the real provider.
- **Secrets never leave.** No credential, API key, SMTP setting, MCP server secret, approver address or channel id is
  written to the file; credential ids become a comment naming the environment variable to set.
- **Editor panel:** **View as Python** in the editor toolbar and the command palette opens a read-only code panel
  (CodeMirror Python, as the Code node editor) beside the canvas, for the open version: **Copy**, **Download .py**
  (`<workflow-name>.py`). Clicking a node scrolls to and highlights its function; a node without code of its own (Start,
  End, Note) highlights its edges or comment.
- **API:** `GET /api/workflows/{wid}/export/python?version=N` returns the file as text with a download filename; same
  view permission as reading the graph; the shared error envelope for errors, new codes in the catalogue, the docs and
  both locales.
- **Verification in the test suite:** for every built-in template and a set of fixture graphs (parallel branches, join,
  for each, subgraph, reducers, retry), the generated file compiles and, run with the mock in a subprocess, visits the
  same nodes in the same order as the studio run with the mock, Human answers taken from the template's test cases.
- **Handbook** (en, vi): an "Export to Python" page with the canvas → code table, a screenshot of the panel, and how to
  run the file, in the Guide section; linked from the
  editor page and the quickstart's "Next steps".

### Out Of Scope

- Importing the edited `.py` back to the canvas (repository import exists for code → canvas; it is a separate flow).
- A full project export (several files, `langgraph.json`, Dockerfile, LangGraph Platform deployment).
- The studio's runtime extras: trace events, the side-effect ledger, run recovery, deadlines and reminders, approval
  channels, cost tracking, node timeouts (written as a comment only: LangGraph has no blocking-node timeout).
- Working code for Retriever, MCP and Send email: they need studio services (knowledge base, MCP sessions, SMTP
  credentials), so they stay stubs.
- Export of imported LangGraph repositories (they are code already).
- Editing the code in the panel.

## Stakeholders Or Users

- People learning LangGraph, who build on the canvas and read the matching code.
- Authors who prototype on the canvas and continue in their own Python project.

## Current Context

- Compiler: `backend/app/engine/compiler.py` (`compile_workflow`, `pick_branch`), node executors
  `engine/nodes.py`, `decisions.py`, `foreach.py`, `emails.py`, reducers `engine/reducers.py`, policies
  `engine/node_policy.py`, templating `engine/templating.py`, mock model `engine/llm.py`, built-in tools
  `engine/tools.py`, subgraph expansion `engine/subgraphs.py`, validation `engine/validator.py`.
- Versions: `WorkflowService.get_version` (REQ-0005). Test cases: REQ-0042 (`services/workflow_test_service.py`).
- Repository import (code → canvas): REQ-0001, REQ-0009, `engine/repo_import.py`.
- Editor: toolbar and command palette (REQ-0018), CodeMirror Python already in `frontend/package.json` (Code node,
  TASK-0055).
- Node types: `validator.TYPES` — start, llm, tool, condition, end, human, join, subgraph, subgraph_exit, retriever,
  mcp, note, foreach, decision, email.

## Desired Behavior

- A learner opens the Router template and clicks **View as Python**. The panel shows `class State(TypedDict)`, a
  `classify` function that calls `call_llm`, a `route_by_category` router, and
  `builder.add_conditional_edges("classify", route_by_category, {"billing": "billing", ...})`. They click the Billing
  node on the canvas; the panel scrolls to `def billing(state)`.
- They download `router.py`, run `pip install langgraph` and `python router.py`: the steps print with the mock model.
  With `OPENAI_API_KEY` set and `pip install langchain-openai`, the same file calls the real model.
- The Leave request file stops at the manager node with `interrupt(...)`; the `__main__` block resumes it with
  `Command(resume="approved")` and finishes on the approved branch.
- They change a prompt and save version 3; the file of version 3 differs from version 2 only in that prompt.

## Business Rules

- The file never holds a secret (credentials, keys, SMTP, MCP secrets, approver addresses, channel ids).
- Same graph, same file.
- Anyone who can view the workflow can view and download its code.
- The file runs offline with the mock by default; a real model is opt-in through environment variables.

## Constraints

- Backend layers (DEC-0009): the generator is engine code with no I/O; a service loads the version and checks access;
  the router returns the text. No schema change.
- The generated file depends on `langgraph` only (plus `httpx` when an HTTP Tool node exists, and a LangChain provider
  package for real models); it does not import anything from Superstep.
- The generated file passes `python -m py_compile` and a basic lint (no unused imports).
- shadcn components and theme tokens; en and vi locale keys identical; no UI text in components.

## Acceptance Criteria

- Every built-in template and each fixture graph exports a file that compiles and, run with the mock, visits the same
  nodes in the same order as the studio's mock run (Human answers from the template's test cases).
- Each node type in the mapping table is exported as described; a test asserts no credential value or id-bound secret
  appears in the output.
- Exporting the same version twice gives byte-identical files; two versions differing in one prompt differ in one
  line.
- The editor panel shows the code for the open version, highlights the selected node's function, copies, and downloads
  `<name>.py`; viewers can open it; imported repositories have no such option.
- The API returns the file with view permission and the shared envelope for errors.
- The handbook page (en, vi) with screenshot builds strictly and passes the image check.
- pytest (SQLite and Postgres), lint, typecheck, vitest, build and e2e pass.

## Edge Cases

- Labels that are not valid Python names, duplicate labels, Python keywords (`class`, `return`), Vietnamese labels
  with diacritics: function names are slugged and made unique; the original label stays in a comment.
- Prompts with quotes, triple quotes, backslashes or `{` `}`: written as safe string literals.
- A Code node whose code does not parse: exported as written, with a comment that the studio rejects it too.
- A graph that fails validation: the export still works when it can be built, else an error names the problem (same
  messages as the run).
- A subgraph whose child workflow the viewer cannot read, or nested five deep: an error, as when running.
- A built-in Tool function that no longer exists: a stub with a `TODO`.
- A Condition with no default and a value that matches no label: the file raises the same error as the studio.

## Assumptions

- LangGraph's `interrupt` / `Command(resume=...)` and `MemorySaver` are the idioms a learner should see, even though
  the studio pauses Human nodes its own way (DEC-0013).
- Readability wins over exact runtime parity: the node path matches with the mock, but retries, timeouts and side
  effects are the learner's to finish.

## Open Questions

Answered by the owner on 2026-10-22 (all three proposed options); the owner accepted the requirement the same day.

- **Q1. How runnable is the file?** Runnable: offline with the mock by default, a real model through environment
  variables (`init_chat_model`).
- **Q2. Language of the explanatory comments.** English always.
- **Q3. Subgraph nodes.** The child workflow as its own compiled graph (`build_<child>()`), added as a node.

## Related Artifacts

- `vision.md` (Goals: learning aid for LangGraph concepts)
- `.factory-state/artifacts/REQ-0009-sandboxed-imports.md` (repository import, code → canvas)
- `.factory-state/artifacts/REQ-0042-workflow-tests.md` (test cases used as example inputs and in verification)
- `roadmap.md`
