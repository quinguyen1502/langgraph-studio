# Requirement

## Metadata

- Project: langgraph-studio
- Requirement ID: REQ-0012
- Status: Proposed
- Owner: Thái Quí Nguyễn
- Created: 2026-10-16
- Updated: 2026-10-16
- Source: project-specs.md (Post-MVP Scope)

## Summary

RBAC and workflow sharing. Introduce roles (admin, editor, viewer) and sharing of workflows with users or groups.

## Problem Or Opportunity

Introduce roles (admin, editor, viewer) and sharing of workflows with users or groups.

## Scope

### In Scope

- Roles, share dialog, permission checks on all APIs and WebSocket

### Out Of Scope

- SSO (could follow)

## Stakeholders Or Users

- Internal developers and learners using LangGraph Studio
- Project owner (administrator)

## Current Context

- Single-owner model in `workflows.owner`

## Desired Behavior

Introduce roles (admin, editor, viewer) and sharing of workflows with users or groups.

## Business Rules

- None

## Constraints

- Mock/offline mode must keep working without API keys.
- Must not break existing auth/ownership rules.

## Acceptance Criteria

- A viewer can open and run but not edit a shared workflow
- An editor can edit; only owner/admin can delete or share
- All existing ownership tests still pass

## Edge Cases

- Missing credentials or unavailable external services produce clear `error` events.

## Assumptions

- Stack direction in `project-specs.md` (Preferred) remains in place.

## Open Questions

- Is SSO (Google/Microsoft) required with RBAC?

## Related Artifacts

- `project-specs.md`
- `.factory-state/artifacts/ARCH-0001-current-architecture.md`
- `.factory-state/artifacts/DISC-0001-project-context.md`
