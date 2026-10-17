# Decision

## Metadata

- Project: langgraph-studio
- Decision ID: DEC-0015
- Task ID: TASK-0008
- Requirement: REQ-0005
- Status: Accepted (owner approved phase 2; details chosen KISS by the agent)
- Date: 2026-10-16

## Context

REQ-0005 has no open questions. These implementation choices were still needed.

## Decisions

1. **Storage**: a separate `workflow_versions` table holds the full workflow JSON per version (no deltas). `workflows` stays the "latest" row, so existing reads are unchanged. Versions are numbered 1..n per workflow.
2. **What creates a version**: any write whose stored JSON differs from the latest version, through one write path (save, rename, duplicate, import, seed, restore). Saving identical content does not create a version, which avoids noise from repeated Ctrl+S.
3. **Migration**: every existing workflow gets v1 with its current data, its owner as author and `updated` as the time. The SQL works on both SQLite and Postgres, and the migration is idempotent.
4. **Rollback = restore as new version**: the graph (nodes, edges, state) of vN is copied into a new latest version with the note "Restored from vN". History is never rewritten or deleted. The **current name is kept**, so a restore cannot break the per-owner unique-name rule. If vN equals the current content, nothing new is created.
5. **Run ↔ version**: `runs.workflow_version` is the latest version when the executed workflow matches it in content (node positions and name ignored), otherwise NULL, shown as "unsaved". API-triggered runs always use the stored workflow, so they get the latest version. Old runs stay NULL.
6. **Diff**: structural, on the server (`/versions/diff?a&b`): nodes and edges by id, state by name; added, removed and changed with before/after for each changed field; position-only changes are listed as `moved`. No visual graph overlay (KISS).
7. **Retention**: versions are kept forever and deleted together with the workflow. No pruning.
8. **Errors**: a new code, `VERSION_NOT_FOUND` (404). A workflow the user doesn't own keeps returning `WORKFLOW_NOT_FOUND`.

## Out of scope

Branching or merging of versions (REQ-0005), named tags, and pruning.
