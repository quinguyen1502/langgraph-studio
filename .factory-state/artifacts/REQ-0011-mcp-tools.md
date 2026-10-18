# Requirement

## Metadata

- Project: langgraph-studio
- Requirement ID: REQ-0011
- Status: Implemented
- Owner: Thái Quí Nguyễn
- Created: 2026-10-16
- Updated: 2026-10-18
- Source: project-specs.md (Post-MVP Scope)

## Summary

MCP tools in Tool node. Tool nodes can call tools exposed by configured MCP servers.

## Problem Or Opportunity

Tool nodes can call tools exposed by configured MCP servers.

## Scope

### In Scope

- MCP server registry (stdio/http)
- Tool discovery and selection in config panel

### Out Of Scope

- Hosting MCP servers

## Stakeholders Or Users

- Internal developers and learners using LangGraph Studio
- Project owner (administrator)

## Current Context

- Tool nodes support HTTP or registered Python functions only

## Desired Behavior

Tool nodes can call tools exposed by configured MCP servers.

## Business Rules

- None

## Constraints

- Mock/offline mode must keep working without API keys.
- Must not break existing auth/ownership rules.

## Acceptance Criteria

- A configured MCP server's tools are listed in the Tool node config
- Running the node calls the MCP tool and writes the result to the output field
- MCP failures surface as node error events

## Edge Cases

- Missing credentials or unavailable external services produce clear `error` events.

## Assumptions

- Stack direction in `project-specs.md` (Preferred) remains in place.

## Open Questions

- Resolved 2026-10-17 (owner): none bundled; a generic stdio + HTTP registry, discovery and an MCP tool node, secrets encrypted, sandbox notes. See DEC-0022.

## Related Artifacts

- `project-specs.md`
- `.factory-state/artifacts/ARCH-0001-current-architecture.md`
- `.factory-state/artifacts/DISC-0001-project-context.md`
- Delivered by `.factory-state/tasks/done/TASK-0013-integrate-mcp-tools-as-tool-node-source.md`, merged to `develop`.
