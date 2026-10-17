# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0029
- Status: backlog
- Owner:
- Created: 2026-10-17
- Updated: 2026-10-17
- Requirement IDs: REQ-0012
- Design IDs: DEC-0024
- Architecture IDs: ARCH-0001

## Objective

Resolve the open issues of Phase 3 (DEC-0023 "Consequences / open", REV-0020, DEC-0022 subgraph leftovers).

## Scope

### In Scope

- Teams: create, members, share a workflow with a team at viewer/editor role (best of direct and team shares wins).
- Ownership transfer by the owner or an admin; credential / knowledge base / MCP references re-bound to the new owner's resources or flagged.
- Audit log of role, activation, share, team, ownership, deletion and policy changes; admin Activity page with category, period and text filters.
- User deletion (anonymize or delete) requiring owned workflows to be reassigned first.
- Admin policy for which roles may use org-wide approval channels and MCP servers at run time (default editors + admins).
- Readable validation names for nodes inside subgraphs; delete of a workflow used as a subgraph blocked with the dependents list (force possible); note on the parent's versions when a child changed.

### Out Of Scope

- Slack Enterprise Grid (org-wide installs) — documented in DEC-0024.
- SSO / SCIM, custom roles, nested teams.

## Inputs

- `.factory-state/decisions/DEC-0023-rbac-sharing.md`
- `.factory-state/artifacts/REV-0020-task-0014.md`

## Acceptance Criteria

- Tests on SQLite and Postgres + Redis, e2e, migration 0022 on both databases.
- New error codes in the catalog, docs/api-errors.md and en/vi.
- Screenshots in 4 variants and contact sheet.
