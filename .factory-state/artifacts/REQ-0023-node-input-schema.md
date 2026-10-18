# Requirement

## Metadata

- Project: langgraph-studio
- Requirement ID: REQ-0023
- Status: Implemented
- Owner: Thái Quí Nguyễn
- Created: 2026-10-18
- Updated: 2026-10-18
- Source: owner request 2026-10-18 to continue the leftover plan. The next product slice is a per-node input schema.

## Summary

A working node can list the state fields it receives. LangGraph then passes only those fields into the node. Leaving the list off passes the whole state, as today.

## Problem Or Opportunity

Every working node currently sees the whole workflow state, including fields it does not use.

## Scope

### In Scope

- A field list on LLM, Retriever, Tool, MCP, and Human nodes.
- Validation that each name exists in the workflow state, and that the value is a list of those names.
- `StateGraph.add_node(..., input_schema=...)` built from the same field types as the graph state.

### Out Of Scope

- Start, End, Condition, Join, Subgraph, and imported code nodes. The panel is hidden there. A list pasted into their JSON is still validated and applied.
- `Command`, `Send`, `error_handler`, and `defer`.
- Checking that a prompt only mentions the selected fields.

## Stakeholders Or Users

- Workflow authors who want a node to read part of the state

## Current Context

- State fields live on the workflow. Node execution settings already sit in the config panel for the five working types.
- LangGraph 1.2.16 filters the dict passed to the node function when `input_schema` is set. The rest of the state stays on the graph.

## Desired Behavior

- All switches off, or no list, means the node sees the whole state.
- One or more switches on means the node function sees only those fields.
- A name that is not a state field fails validation with a message that names the node.

## Business Rules

- UI strings live in `en.json` and `vi.json` with the same keys.
- The list stored on the node follows the state-field order.

## Constraints

- Engine only. No new API error code. shadcn Switch and theme tokens.

## Acceptance Criteria

- The Input fields section is on LLM, Retriever, Tool, MCP, and Human, and absent on Start.
- A chosen list is still there after selecting another node and coming back.
- An unknown name, a non-list, and a duplicate fail validation and the message names the node.
- A tool node limited to `message` does not see `out` when both are in the run input. With the list omitted it sees both.

## Edge Cases

- An empty list is the same as omitting it.
- A field removed from the state after it was selected fails validation until the list is changed.

## Assumptions

- The owner approved this slice by saying to continue the leftover plan. `factory ready` does not exit 0 on this machine. Proceed as with TASK-0033.
- One task.

## Open Questions

- None

## Related Artifacts

- `.factory-state/artifacts/REQ-0019-node-execution-settings.md`
- `.factory-state/artifacts/ARCH-0001-current-architecture.md`
- `.factory-state/tasks/done/TASK-0035-node-input-schema.md`
- `.factory-state/artifacts/REV-0034-task-0035.md`
- `.factory-state/artifacts/QA-0034-task-0035.md`
