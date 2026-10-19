# Concepts

## Workflow

A workflow is one JSON document: a name, a state schema, nodes and edges.

```json
{"name": "Support triage",
 "state": [{"name": "message", "type": "string"}, {"name": "answer", "type": "string"}],
 "nodes": [{"id": "n1", "type": "llm", "position": {"x": 0, "y": 0},
            "data": {"label": "Reply", "model": "gpt-4o-mini",
                     "prompt": "Hi {{state.message}}", "output_field": "answer"}}],
 "edges": [{"id": "e1", "source": "start", "target": "n1"}]}
```

The backend compiles it into a LangGraph `StateGraph`: each node becomes a
graph node, each edge a transition, and a Condition node becomes a
conditional edge. The JSON is the source of truth; the editor only writes it.

## State

The state is a typed record shared by every node. A node reads fields
through `{{state.field}}` references and writes its result to one
`output_field`. When several parallel branches write the same field, the
field needs a **reducer**: `append` for a list, `merge` for an object, `add`
for a number. The default is `replace`. See [State and references](../guide/state.md).

## Nodes and edges

| Kind | Nodes |
| --- | --- |
| Model calls | LLM, Decision (Jev) |
| Data and tools | Tool (function, HTTP or Python code), MCP tool, Retriever, Send email |
| Control flow | Condition, For each, Join, Subgraph |
| People | Human |
| Boundaries | Start, End |

An edge from one node to several targets runs the branches in the same
superstep. A Condition picks one outgoing edge by its label. See
[Nodes](../guide/nodes.md).

## Run

A run is one execution of a saved (or unsaved) graph with a JSON input. It
streams events such as `run_started`, `node_started`, `node_token`,
`node_finished`, `run_waiting`, `run_paused`, `error` and `run_finished`. The final statuses are `ok`, `error`, `cancelled`,
`timeout` and `paused`; a run waiting at a Human node is `waiting`, and one
that waited too long becomes `expired`.

## Superstep

LangGraph executes the graph in **supersteps**. Every node that is ready runs
in the same superstep; their writes are merged by the reducers before the next
one starts. **Step** in the editor runs exactly one superstep, then pauses.

## Checkpoint

After each superstep the run's state is saved as a checkpoint in the
database. A Human node, a paused step, a worker crash or a restart resumes
from the last checkpoint instead of starting again.

## Effectively-once side effects

Every LLM and Tool execution has an idempotency key fixed by run, node and
iteration. A finished side-effect node is recorded in a ledger, so a
recovered run replays its result (`reused` in the trace) instead of calling
the service again. HTTP tools send `Idempotency-Key` too. See
[Architecture](../reference/architecture.md).

## Version

Each save that changes the graph writes an immutable version. Runs record
the version they used. See [Versions](../guide/versions.md).
