# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0035
- Status: done
- Phase: node input schema
- Owner:
- Created: 2026-10-18
- Updated: 2026-10-18
- Requirement IDs: REQ-0023
- Design IDs:
- Architecture IDs: ARCH-0001

## Objective

Let a working node choose which state fields LangGraph passes in.

## Scope

### In Scope

- `input_fields` on the node, the config switches, validator messages, and `add_node(input_schema=)`

### Out Of Scope

- The panel on Start, End, Condition, Join, Subgraph, and code nodes
- Prompt-variable checks against the selected list

## Inputs

- `.factory-state/artifacts/REQ-0023-node-input-schema.md`

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0023-node-input-schema.md`
- Review: `.factory-state/artifacts/REV-0034-task-0035.md`
- QA: `.factory-state/artifacts/QA-0034-task-0035.md`

## Expected Outputs

- Engine behaviour covered by `backend/tests/test_node_policy.py`
- Switches in the config panel

## Implementation Notes

- Blank or `[]` does not pass `input_schema`. The node keeps seeing the whole state.
- The schema uses the same annotations as the graph `TypedDict`, so the channel type matches.

## Constraints

- Routers stay out of this change. The engine does not import FastAPI.

## Dependencies

- TASK-0031 is on `develop`. This branch starts there, not on the unmerged record or editor branches.

## Acceptance Criteria

- Same as REQ-0023.

## Validation Plan

- `cd backend && /tmp/lgs-qa-venv/bin/python -m pytest -q tests/test_node_policy.py tests/test_compiler.py tests/test_layers.py`
- `cd frontend && npx tsc -b`
- `git diff --check`

## Assumptions

- `factory ready` did not exit 0 here. The owner asked to continue anyway.

## Open Questions

- None

## Activity Log

- 2026-10-18: Owner said to continue. REQ-0023 approved from the leftover plan. Task started on `factory/task-0035-node-input-schema`.
- 2026-10-18: Policy tests, compiler tests, and layer tests passed (15). `npx tsc -b` passed. The example LLM node showed the switches; Start did not. Moved to review. Draft PR #38 opened into `develop`: https://github.com/quinguyen1502/langgraph-studio/pull/38
- 2026-10-18: Rebased onto `develop` after PR #37 merged. Owner asked to finish and merge. REV-0034 has no blocking findings. QA-0034 passed. Task set to done.

## Handoff Notes

- Draft PR into `develop`. Do not merge until the owner asks.
