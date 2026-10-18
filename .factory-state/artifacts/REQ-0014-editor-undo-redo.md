# Requirement

## Metadata

- Project: langgraph-studio
- Requirement ID: REQ-0014
- Status: Implemented
- Owner: Thái Quí Nguyễn
- Created: 2026-10-17
- Updated: 2026-10-18
- Source: owner request 2026-10-17 (Phase 5: Editor UX)

## Summary

An editor history stack so node/edge/config changes can be undone and redone.

## Problem Or Opportunity

A wrong delete or drag in the editor cannot be reverted except by reloading or restoring a version.

## Scope

### In Scope

- History of editor snapshots (nodes, edges, state schema, node config), coalescing drags and typing bursts, capped size (e.g. 100)
- Undo (Mod+Z) / redo (Mod+Shift+Z, Mod+Y) via the TASK-0023 registry, plus toolbar buttons with disabled states
- History resets on load / version restore; unsaved-changes tracking stays correct after undo back to the saved state

### Out Of Scope

- Server-side history (versions already cover saved states)
- Collaborative editing

## Stakeholders Or Users

- Workflow authors using the LangGraph Studio editor

## Current Context

- React Flow editor (`frontend/src/pages/Editor.tsx`), shadcn/Tailwind UI, en/vi i18n

## Desired Behavior

An editor history stack so node/edge/config changes can be undone and redone.

## Business Rules

- Strict shadcn (tokens only), en/vi texts, keyboard and screen-reader accessible

## Constraints

- Mock/offline mode must keep working without API keys.

## Acceptance Criteria

- Add, delete, move, connect and config edits are each undoable and redoable
- A drag is one step, not one per pixel; typing in a field is coalesced
- Undo back to the saved snapshot clears the unsaved marker
- Unit tests for the history reducer; e2e for delete → undo → redo

## Open Questions

- None yet

## Related Artifacts

- Delivered by `.factory-state/tasks/done/TASK-0024-editor-undo-and-redo-history.md`, merged to `develop`.
