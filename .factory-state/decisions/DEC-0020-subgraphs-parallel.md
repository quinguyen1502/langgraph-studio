# Decision

## Metadata

- Decision ID: DEC-0020
- Status: Accepted (implementation in review)
- Date: 2026-10-17
- Related: TASK-0011, REQ-0006, ARCH-0001

## Context

REQ-0006 asks for subgraph nodes that embed another saved workflow and for fan-out/fan-in parallel branches whose outputs merge through declared reducers. The open question was which reducers to support.

## Decisions

### Reducers (answering the open question)
- Each state field may declare `reducer`: `replace` (default), `append` (type `list`; a non-list output is appended as one item), `merge` (type `object`, shallow), `add` (`number` / `integer`).
- They are LangGraph channel reducers (`Annotated[type, fn]`), and the runtime applies the same functions to its own state tracking, so trace payloads match the graph state (`engine/reducers.py`).
- Static check: when a node fans out to several nodes that write the same field and the field has no reducer, the workflow is invalid. Otherwise LangGraph would fail at run time with a concurrent-update error.

### Parallel branches and Join
- Any non-Condition node may have several outgoing edges. Each edge is a branch, and the branches run in the same superstep. The earlier "only one outgoing edge" rule is removed.
- New `join` node (pass-through). Its incoming edges are compiled into one LangGraph waiting edge (`add_edge([sources], join)`), so it runs once after every branch, even branches of different lengths. It needs at least two incoming edges, and a Condition must not feed it directly, because it would then wait for a branch that may never run.
- Without a Join, a node with several incoming edges runs once per arriving branch (LangGraph semantics, documented).
- Send-API map-reduce stays out of scope.

### Subgraph nodes: expanded inline
- `subgraph` node, `data.workflow_id`. Before validation and compilation the child workflow is expanded into the parent (`engine/subgraphs.py`). Child node ids are prefixed `sub/inner`, labels `Sub › Inner`. The subgraph node becomes the pass-through entry, and every child End becomes one exit node `sub/__exit` that carries the subgraph node's outgoing edges. This works recursively.
- Why inline rather than a compiled LangGraph subgraph: inner nodes then get the existing trace events, Human pauses, progress checkpoints, recovery, idempotency keys and node-result ledger with no new code paths.
- State is shared by field name. Child fields that are missing in the parent are added; the same name with a different type is an error.
- References resolve only to workflows the user owns, until RBAC (TASK-0014). Missing workflows, imported (code) workflows, cycles (including self-references) and nesting deeper than 5 levels are validation errors, reported when saving or validating and as `WORKFLOW_INVALID` when running.
- The expanded graph is what runs and what checkpoints store. A waiting or recovered run therefore continues on the same graph even if the child workflow changes meanwhile.
- UI: the canvas maps `sub/inner` events to the subgraph node (status), and the trace shows each inner node as its own row.

## Consequences
- Validation errors of inner nodes name the prefixed ids, for example `sub/sum`.
- The run version tag still refers to the parent workflow only. A child edit does not create a parent version.
- Deleting a workflow that others embed makes their runs fail with `WORKFLOW_INVALID` until the reference is changed.
