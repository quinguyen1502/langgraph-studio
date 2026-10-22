# Decision Record

## Metadata

- Project: superstep
- Decision ID: DEC-0045
- Status: Accepted
- Owner: Thái Quí Nguyễn
- Created: 2026-10-22
- Updated: 2026-10-22
- Related Requirements: REQ-0043
- Related Architecture: DEC-0009 (layers), DEC-0013 (human in the loop), DEC-0038 (For each), DEC-0039 (Decision
  nodes), DEC-0044 (test cases)
- Related Tasks: TASK-0070, TASK-0071, TASK-0072

## Context

REQ-0043 exports a workflow as one LangGraph Python file for people learning how a graph is written in code. The
compiler (`engine/compiler.py`) already builds a `StateGraph`, but around studio services (trace, side-effect ledger,
ports, policies, resume handling), so it is not code to learn from. The owner chose a file that runs on its own with a
mock model (Q1), English comments (Q2) and subgraphs as their own graphs (Q3).

## Decision

1. **A generator, not the compiler.** `engine/python_export.py` writes source text from the workflow JSON: a pure
   function with no I/O (`to_python(wf, name, version, children, example) -> Export(code, nodes, names, filename)`).
   `WorkflowService.python` loads the version (latest by default), checks view access, loads subgraph children with
   the viewer's access (as a run does) and takes the first test case as the example. Routes:
   `GET /api/workflows/{wid}/python` (JSON: code, filename, version, node line ranges) and
   `GET /api/workflows/{wid}/export/python` (the file, `text/x-python`, `Content-Disposition`). Imported repositories:
   `PYTHON_EXPORT_UNAVAILABLE`.
2. **No secrets.** The graph goes through `templates.sanitize` first (credential, knowledge base, server, channel and
   workflow references blanked, secret-like keys dropped, Human approval reduced to its channel kind, escalation
   addresses dropped). Subgraph references are read from the raw graph before that.
3. **Mapping** (canvas → code):

   | Canvas | Code |
   | --- | --- |
   | State fields | `class State(TypedDict, total=False)`; reducers as `Annotated[type, append_items / merge_objects / add_numbers]` |
   | Start / End | `START` / `END` edges |
   | LLM | `render(PROMPT, state)` then `call_llm(prompt, model)` |
   | Human | `interrupt({"node", "question"})`, resumed with `Command(resume=answer)` |
   | Condition | a pass-through node and `add_conditional_edges(node, route_<node>, {label: target})`; `pick_branch` as in the studio, the default branch or a `ValueError` |
   | Join | a pass-through node and `add_edge([sources], join)` |
   | For each | the studio's loop: a `loop_<node>` position field, `route_<node>` returning `each` / `done` |
   | Decision | `decide(text, question)` per question (the Jev mock offline, `call_llm` with `LLM_PROVIDER`) |
   | Subgraph | the child's own `build_<child>()` compiled graph added as the node; the child has its own `State` class |
   | Tool: function | the registered function's source, with the module constants it uses |
   | Tool: HTTP | `httpx.request(...)`, no redirects |
   | Tool: Code | the node's code inside the node function, then `main(dict(state))` |
   | Retriever, MCP, Send email | stubs `retrieve`, `call_mcp_tool`, `send_email` with a `TODO` (empty result, `None`, a printed dry run) |
   | Note | a comment |
   | Retry, cache, input fields | `RetryPolicy`, `CachePolicy` (+ `InMemoryCache`), `input_schema` |
   | Timeout | a comment (LangGraph cannot stop a node that blocks) |

4. **Runnable offline.** `call_llm` is a copy of the studio's `mock_llm` unless `LLM_PROVIDER` is set; then it calls
   LangChain's `init_chat_model(model, model_provider=LLM_PROVIDER)`. `main()` streams the example input
   (`stream_mode="updates"`, `subgraphs=True`), answers interrupts from `EXAMPLE_ANSWERS` (else asks on the terminal),
   and prints the final state. The helpers (`render`, `render_args`, `mock_llm`, `pick_branch`, `decide`) are written
   out in the file; a test compares them with the engine's so they stay in step.
5. **Names.** Node names are the labels as Python identifiers (diacritics removed, lower case, `_`), unique across
   the file, never a builtin, keyword, helper or state field name (LangGraph refuses a node named like a state key):
   a clash gets `_node`, then `_2`, `_3`. The same name is the function and the LangGraph node.
6. **Deterministic.** Nodes are written breadth first from Start in edge order; positions are not used; no timestamps.
   The same version always gives the same bytes.
7. **Verified against the studio.** `tests/test_python_export.py` runs each exported file in a fresh interpreter
   (`python -I`) and compares the nodes it runs and the final state with the studio's mock run, for every built-in
   template test case and fixture graphs (parallel branches with reducers and policies, For each with a Condition,
   a subgraph with a Human node, every Tool mode, Decision, MCP, Send email, odd labels).

## Consequences

- Known differences, written in the file or the handbook: retries, timeouts, caching and side effects are the
  learner's to finish; a reducer field that a subgraph also writes is combined again when the subgraph returns (the
  studio runs the child's nodes inline); a Decision with a real model uses an LLM prompt, not TypeSafe Jev; Retriever,
  MCP and Send email are stubs.
- A change to `mock_llm`, `pick_branch`, `templating` or the Jev mock must be made in the generator's helpers too;
  the helper test fails otherwise.
- TASK-0071 uses the JSON route's node line ranges to highlight the selected node.
