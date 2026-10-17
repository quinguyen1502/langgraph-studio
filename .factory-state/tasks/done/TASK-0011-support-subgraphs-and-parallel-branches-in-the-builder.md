# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0011
- Previous ID: TASK-0010 (renumbered 2026-10-16, DEC-0007)
- Status: done
- Owner:
- Created: 2026-10-16
- Updated: 2026-10-16
- Requirement IDs: REQ-0006
- Design IDs:
- Architecture IDs: ARCH-0001

## Objective

Implement REQ-0006: Support subgraphs and parallel branches in the builder.

## Scope

### In Scope

- Deliver the in-scope items of `.factory-state/artifacts/REQ-0006-subgraphs-parallel.md`

### Out Of Scope

- Out-of-scope items listed in REQ-0006

## Inputs

- `.factory-state/artifacts/REQ-0006-subgraphs-parallel.md`
- `.factory-state/artifacts/ARCH-0001-current-architecture.md`

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0006-subgraphs-parallel.md`
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

- A workflow containing a subgraph node compiles and runs, emitting events for inner nodes
- Two parallel branches run in the same superstep and their outputs merge via declared reducers
- Cycles between workflows via subgraph references are rejected by validation

## Validation Plan

- `cd backend && .venv/bin/python -m pytest -q`
- `cd frontend && npm run build`
- Manual run of the seeded example

## Assumptions

- Integration branch is `develop`; draft PR, never merged by the agent.

## Open Questions

- Which state reducers must be supported (append list, merge dict)?

## Activity Log

- 2026-10-17: Implemented (DEC-0020, REV-0017, QA-0017); moved to review. Open question resolved: reducers replace/append/merge/add.

- 2026-10-16: Renumbered TASK-0010 -> TASK-0011 per owner re-plan (DEC-0007).
- 2026-10-16: Created task during Factory import/onboarding.

- 2026-10-17: Status set to done to match the done/ folder. Previous Status was `review`. Review REV-0017. QA QA-0017.

## Handoff Notes

- Use branch `factory/task-0011-support-subgraphs-and-parallel-branches-in-the-builder` when implementation begins.
