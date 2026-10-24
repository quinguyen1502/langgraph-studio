# Export to Python

The **Code** tab in the editor shows the workflow as one LangGraph Python file:
the state, one function per node, and the graph built from them. Use it to see
how a graph on the canvas is written in code, or to carry a prototype into your
own project. It can also write the graph as LangGraph.js TypeScript: see
[TypeScript (LangGraph.js)](#typescript-langgraphjs).

![The Code tab with the Manager approval node selected](../images/code-tab.png)

## Open the code

- Open the **Code** tab in the bottom panel, or choose **View as code** in the
  **⋯** menu or the command palette (++ctrl+k++).
- The tab shows the **latest saved version**. Unsaved changes are marked and
  appear after **Save**.
- Select a node on the canvas: its code is highlighted and scrolled into view.
  Start and End point at their `START` and `END` edges.
- **Copy** puts the whole file on the clipboard; **Download .py** saves it,
  named after the workflow.
- Anyone who can open the workflow can see its code. Imported LangGraph
  repositories are code already and have no Code tab.

## Run the file

```bash
pip install langgraph
python leave_request.py
```

The file needs nothing from Superstep. It runs the example input (the first
test case's input when the workflow has one) and prints what each node
returned, then the final state:

```text
[read_the_request] {"details": "[mock:gpt-4o-mini] Answer: I'd like leave ..."}
>> manager_approval: approved
[manager_approval] {"decision": "approved"}
(e-mail not sent) to bo@example.com: Your leave request: approved
...
Final state: {...}
```

- **Models.** LLM nodes use an offline mock by default: no API key, no cost,
  the same answers every time. To call a real model, install LangChain and a
  provider package and name the provider:

    ```bash
    pip install langchain langchain-openai
    export LLM_PROVIDER=openai OPENAI_API_KEY=sk-...
    ```

    `LLM_PROVIDER` is any provider `init_chat_model` knows (`openai`,
    `anthropic`, `ollama`, …); the node's model name is used as written.
- **Human nodes.** `EXAMPLE_ANSWERS` holds the answers from the first test
  case. When a node has no answer left, the file asks on the terminal.
- **Code nodes** run as written, in your Python process, without the studio's
  sandbox. Read them before running a file someone else shared.

## From the canvas to the code

| Canvas | Code |
| --- | --- |
| State fields | `class State(TypedDict, total=False)`; a reducer is `Annotated[type, reducer]` |
| Start and End | `START` and `END` in the edges |
| LLM | `render(PROMPT, state)`, then `call_llm(prompt, model)` |
| Condition | a node that changes nothing, and `add_conditional_edges` with a router function and a label → node map |
| Human | `interrupt(...)` pauses the run; `Command(resume=answer)` continues it |
| Join | a node, and `add_edge([branch, branch], join)`: it runs once all branches finished |
| For each | a loop position field and a router that returns `each` or `done` |
| Decision | `decide(text, question)` for each question |
| Subgraph | the child workflow as its own graph, `build_<child>()`, added as a node |
| Tool: function | the function's code, copied in |
| Tool: HTTP | an `httpx` request |
| Tool: Code | the node's code, inside the node function |
| Retriever, MCP, Send email | stubs with a `TODO`: they need studio services |
| Note | a comment |
| Retry, cache, input fields | `RetryPolicy`, `CachePolicy`, `input_schema` on `add_node` |
| Timeout | a comment: LangGraph cannot stop a node that blocks |

Node functions are named after their labels (`Read the request` →
`read_the_request`). A name that clashes with a state field or a Python name
gets `_node`, for example `decision_node`.

### State and reducers

```python
class State(TypedDict, total=False):
    feedback: list
    item: str
    labelled: Annotated[list, append_items]
    report: str
    sent: dict
    loop_each_piece_of_feedback: int  # loop position of a For each node
```

From the Customer feedback digest template. A node returns only the fields it
changes, and LangGraph merges them into the state. A field without a reducer is
replaced; `labelled` collects one label per piece of feedback.

### A Condition

From the Router template:

```python
def route_route(state: State) -> str:
    """The branch to take after "Route": the edge label that state["intent"] names."""
    value = state.get("intent")
    ...
    label = pick_branch(value, ["billing", "technical", "other"])
    return "other" if label is None else label


builder.add_conditional_edges("route", route_route, {"billing": "billing_answer", "technical": "technical_answer", "other": "general_answer"})
```

### A Human node

From the Leave request template:

```python
def manager_approval(state: State) -> dict:
    answer = interrupt({"node": "manager_approval", "question": render(MANAGER_APPROVAL_PROMPT, state)})
    return {"decision": answer}
```

`interrupt()` stops the run and hands the question to the caller. The graph is
compiled with a checkpointer (`MemorySaver`), so `main()` can resume it with
`graph.stream(Command(resume="approved"), config)`. The node then runs again
from the top, and `interrupt()` returns the answer.

### A Subgraph

```python
def build_review_step():
    builder = StateGraph(ReviewStepState)
    ...
    return builder.compile()


builder.add_node("review", build_review_step())  # a compiled graph is a node of another graph
```

The subgraph has its own state class and shares fields with the parent by name.

## TypeScript (LangGraph.js)

Pick **TypeScript** in the language menu of the Code tab to get the same graph as
one [LangGraph.js](https://langchain-ai.github.io/langgraphjs/) file. The menu
remembers your choice; **Download .ts** saves the file.

```bash
deno run --allow-env --allow-read leave_request.ts
```

The packages are `npm:` imports (`npm:@langchain/langgraph@^1.5`), so Deno
fetches them on the first run and `deno check` type-checks the file. For Node,
drop the `npm:` prefixes and versions, run `npm i @langchain/langgraph
@langchain/core`, then `npx tsx leave_request.ts`.

| Canvas | TypeScript |
| --- | --- |
| State fields | `Annotation.Root({...})`; a reducer is `Annotation({ reducer, default })` |
| LLM | `render(PROMPT, state)`, then `callLlm(prompt, model)`: the mock, or `initChatModel` when `LLM_PROVIDER` is set |
| Condition, For each | `addConditionalEdges` with a router function |
| Human | `interrupt(...)`; `new Command({ resume })` continues the run |
| Join | `addEdge([branch, branch], join)` |
| Decision | `decide(text, question)` for each question |
| Subgraph | `build_<child>()`, a compiled graph added as a node |
| Tool: Code in TypeScript | the node's code as written; its imports move to the top of the file |
| Tool: Code in Python | a stub that throws `not implemented in TS export`: port it |
| Tool: function | a stub that throws: the function is Python on the server |
| Tool: HTTP | `fetch`, without following redirects |
| Retriever, MCP, Send email | stubs with a `TODO`, as in the Python file |
| Retry, cache, input fields, timeout | `retryPolicy`, `cachePolicy`, `input`, `timeout` on `addNode` |

API keys and other settings are read from environment variables
(`LLM_PROVIDER`, `OPENAI_API_KEY`, …), never written in the file. A node that
nothing connects to Start is left out, with a comment: LangGraph.js refuses
unreachable nodes. The Python file has the same kind of stub for TypeScript Code
nodes (`NotImplementedError`).

## What is not in the file

- Credentials, API keys, SMTP settings, knowledge bases, MCP servers, approval
  channels, approvers and escalation addresses.
- Studio features around a run: the trace, run history, recovery after a
  restart, approval channels and deadlines, cost tracking, node timeouts.
- Real Retriever, MCP and Send email calls: the stubs return an empty result,
  nothing, or the message that would have been sent.

Two results can differ from the studio: a Decision node with a real model asks
the LLM instead of TypeSafe Jev, and a field with a reducer that a subgraph also
writes is combined again when the subgraph returns.

## API

`GET /api/workflows/{wid}/python` returns the code, the file name, the version
and the line ranges of each node; `GET /api/workflows/{wid}/export/python`
downloads the file. Both take `?version=n` and `?language=python|typescript`
(`GET /api/workflows/{wid}/code` and `/export/typescript` are the same with a
neutral name). See the
[HTTP API](../reference/api.md).
