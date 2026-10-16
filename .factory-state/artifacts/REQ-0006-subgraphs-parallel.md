# Requirement

## Metadata

- Project: langgraph-studio
- Requirement ID: REQ-0006
- Status: Proposed
- Owner: Thái Quí Nguyễn
- Created: 2026-10-16
- Updated: 2026-10-16
- Source: project-specs.md (Post-MVP Scope)

## Summary

Subgraphs and parallel branches in the builder. Builder supports embedding a saved workflow as a subgraph node and fan-out/fan-in parallel branches.

## Problem Or Opportunity

Builder supports embedding a saved workflow as a subgraph node and fan-out/fan-in parallel branches.

## Scope

### In Scope

- Subgraph node referencing another workflow
- Multiple outgoing edges from LLM/Tool nodes executing in parallel with reducer-based state merge

### Out Of Scope

- Dynamic map-reduce (Send API) in first iteration

## Stakeholders Or Users

- Internal developers and learners using LangGraph Studio
- Project owner (administrator)

## Current Context

- Validation currently forbids >1 outgoing edge from LLM/Tool nodes

## Desired Behavior

Builder supports embedding a saved workflow as a subgraph node and fan-out/fan-in parallel branches.

## Business Rules

- None

## Constraints

- Mock/offline mode must keep working without API keys.
- Must not break existing auth/ownership rules.

## Acceptance Criteria

- A workflow containing a subgraph node compiles and runs, emitting events for inner nodes
- Two parallel branches run in the same superstep and their outputs merge via declared reducers
- Cycles between workflows via subgraph references are rejected by validation

## Edge Cases

- Missing credentials or unavailable external services produce clear `error` events.

## Assumptions

- Stack direction in `project-specs.md` (Preferred) remains in place.

## Open Questions

- Which state reducers must be supported (append list, merge dict)?

## Related Artifacts

- `project-specs.md`
- `.factory-state/artifacts/ARCH-0001-current-architecture.md`
- `.factory-state/artifacts/DISC-0001-project-context.md`
