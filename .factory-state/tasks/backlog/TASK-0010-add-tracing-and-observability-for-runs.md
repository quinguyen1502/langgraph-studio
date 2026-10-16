# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0010
- Previous ID: TASK-0009 (renumbered 2026-10-16, DEC-0007)
- Status: backlog
- Owner:
- Created: 2026-10-16
- Updated: 2026-10-16
- Requirement IDs: REQ-0010
- Design IDs:
- Architecture IDs: ARCH-0001

## Objective

Implement REQ-0010: Add tracing and observability for runs.

## Scope

### In Scope

- Deliver the in-scope items of `.factory-state/artifacts/REQ-0010-observability.md`

### Out Of Scope

- Out-of-scope items listed in REQ-0010

## Inputs

- `.factory-state/artifacts/REQ-0010-observability.md`
- `.factory-state/artifacts/ARCH-0001-current-architecture.md`

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0010-observability.md`
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

- Each run produces a trace with one span per node including duration and status
- Tracing is disabled cleanly when no exporter is configured

## Validation Plan

- `cd backend && .venv/bin/python -m pytest -q`
- `cd frontend && npm run build`
- Manual run of the seeded example

## Assumptions

- Integration branch is `main` (see DISC-0001).

## Open Questions

- LangSmith, OTel collector, or both?

## Activity Log

- 2026-10-16: Renumbered TASK-0009 -> TASK-0010 per owner re-plan (DEC-0007).
- 2026-10-16: Created task during Factory import/onboarding.

## Handoff Notes

- Use branch `factory/task-0010-add-tracing-and-observability-for-runs` when implementation begins.
