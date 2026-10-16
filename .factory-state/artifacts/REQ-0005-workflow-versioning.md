# Requirement

## Metadata

- Project: langgraph-studio
- Requirement ID: REQ-0005
- Status: Proposed
- Owner: Thái Quí Nguyễn
- Created: 2026-10-16
- Updated: 2026-10-16
- Source: project-specs.md (Post-MVP Scope)

## Summary

Workflow versioning, diff and rollback. Every save creates an immutable version; users can view history, diff two versions and roll back.

## Problem Or Opportunity

Every save creates an immutable version; users can view history, diff two versions and roll back.

## Scope

### In Scope

- Version table, version list UI, JSON/graph diff, rollback

### Out Of Scope

- Branching/merging of versions

## Stakeholders Or Users

- Internal developers and learners using LangGraph Studio
- Project owner (administrator)

## Current Context

- `POST /api/workflows` overwrites the single row

## Desired Behavior

Every save creates an immutable version; users can view history, diff two versions and roll back.

## Business Rules

- None

## Constraints

- Mock/offline mode must keep working without API keys.
- Must not break existing auth/ownership rules.

## Acceptance Criteria

- Each save creates a new version with author and timestamp
- Run history records the version that executed
- Rollback restores a previous version as a new latest version

## Edge Cases

- Missing credentials or unavailable external services produce clear `error` events.

## Assumptions

- Stack direction in `project-specs.md` (Preferred) remains in place.

## Open Questions

- None

## Related Artifacts

- `project-specs.md`
- `.factory-state/artifacts/ARCH-0001-current-architecture.md`
- `.factory-state/artifacts/DISC-0001-project-context.md`
