# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0012
- Status: backlog
- Owner:
- Created: 2026-10-16
- Updated: 2026-10-16
- Requirement IDs: REQ-0011
- Design IDs:
- Architecture IDs: ARCH-0001

## Objective

Implement REQ-0011: Integrate MCP tools as Tool node source.

## Scope

### In Scope

- Deliver the in-scope items of `.factory-state/artifacts/REQ-0011-mcp-tools.md`

### Out Of Scope

- Out-of-scope items listed in REQ-0011

## Inputs

- `.factory-state/artifacts/REQ-0011-mcp-tools.md`
- `.factory-state/artifacts/ARCH-0001-current-architecture.md`

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0011-mcp-tools.md`
- Architecture: `.factory-state/artifacts/ARCH-0001-current-architecture.md`
- Discovery: `.factory-state/artifacts/DISC-0001-project-context.md`

## Expected Outputs

- Implementation, tests, README update
- Design/architecture artifact if the requirement changes boundaries

## Constraints

- Mock mode and existing tests must keep passing

## Dependencies

- TASK-0002 (CI) recommended first

## Acceptance Criteria

- A configured MCP server's tools are listed in the Tool node config
- Running the node calls the MCP tool and writes the result to the output field
- MCP failures surface as node error events

## Validation Plan

- `cd backend && .venv/bin/python -m pytest -q`
- `cd frontend && npm run build`
- Manual run of the seeded example

## Assumptions

- Integration branch is `main` (see DISC-0001).

## Open Questions

- Which MCP servers are needed first?

## Activity Log

- 2026-10-16: Created task during Factory import/onboarding.

## Handoff Notes

- Use branch `factory/task-0012-integrate-mcp-tools-as-tool-node-source` when implementation begins.
