# Decision

## Metadata

- Decision ID: DEC-0024
- Status: Accepted (implementation in review)
- Date: 2026-10-17
- Related: TASK-0029, DEC-0023, DEC-0022, DEC-0019, ARCH-0001

## Context
DEC-0023 left teams, ownership transfer, an audit log, user deletion and viewer access to org resources open; DEC-0022 left subgraph naming and delete-safety leftovers.

## Decisions

### Teams
- `teams`, `team_members`, `workflow_team_shares` (migration `0022_teams_audit`). Admins manage teams (Settings → Teams). Owners/admins share a workflow with a team at viewer or editor.
- Effective share role = best of the direct share and all team shares (`permissions.best_share`); the `viewer` account role still caps at view. `AccessService` stays the single check.

### Ownership transfer
- New action `transfer` (owner + admin). Target must be an active editor or admin. `GET /transfer` previews references (credential, knowledge base, MCP server, subgraph) the target cannot use; `POST` re-binds the chosen ones to the target's own resources, keeps the rest **flagged** (listed in the version note and returned), optionally keeps the old owner as editor.
- Subgraph references are never re-bound (the target gets view access needs through sharing, not copying).

### Audit log
- `audit_events` (actor, action, target type/id/label, JSON details, time). Written by the services that make the change (user, share, team, ownership, policy, delete) — no route-level logging. `GET /api/admin/audit` with category, period (24h/7d/30d), text search, paging; Settings → Activity.

### User deletion
- `DELETE /api/admin/users/{id}` with `mode` `anonymize` (tombstone row `deleted-…@deleted.invalid`, deactivated, runs kept) or `delete` (row and their runs removed). Both purge personal credentials, knowledge bases, MCP servers, channels, tokens, shares and team membership. Owned workflows must be reassigned (`reassign_to`, via the same transfer logic) or the call fails with `USER_HAS_WORKFLOWS`. Self and last-admin guards apply.

### Org resources at run time
- Setting `org_resources_roles` (`studio_settings`), default `admin, editor`; admin always included. Checked against the **actor** of the run: org MCP servers raise `ORG_RESOURCE_NOT_ALLOWED`, org approval channels are skipped and audited. Lists expose `org_usable` for a UI notice.

### Subgraph leftovers
- Validation/compile errors inside expanded subgraphs read `Parent › Inner` instead of internal ids.
- Deleting a workflow used as a subgraph returns `WORKFLOW_IN_USE` with `details.dependents` (hidden ones anonymised); `?force=true` deletes anyway.
- Version list carries `children_changed`, computed at read time (no stored state).

### Out of scope: Slack Enterprise Grid
- Org-wide Grid installs (`team` vs `enterprise` ids, per-workspace channel resolution) are not supported; a Grid workspace works as a normal single-workspace install. Revisit with a requirement.

## Error codes
TEAM_NOT_FOUND, TEAM_NAME_REQUIRED, TEAM_NAME_TAKEN, TEAM_MEMBER_NOT_FOUND, TRANSFER_SAME_OWNER, TRANSFER_TARGET_ROLE, TRANSFER_REBIND_INVALID, USER_HAS_WORKFLOWS, USER_DELETE_MODE_INVALID, WORKFLOW_IN_USE, ORG_RESOURCE_NOT_ALLOWED.

## Consequences / open
- No nested teams, no custom roles, no SSO/SCIM group sync.
- The audit log has no retention/export yet.
- Flagged references after a transfer must be fixed by hand in the editor.
