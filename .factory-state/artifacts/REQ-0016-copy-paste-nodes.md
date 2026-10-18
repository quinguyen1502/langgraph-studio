# Requirement

## Metadata

- Project: langgraph-studio
- Requirement ID: REQ-0016
- Status: Implemented
- Owner: Thái Quí Nguyễn
- Created: 2026-10-17
- Updated: 2026-10-18
- Source: owner request 2026-10-17 (Phase 5: Editor UX) — suggested by the factory agent, approved by the owner 2026-10-17

## Summary

Copy/cut/paste and duplicate selected nodes (with the edges between them), also across workflows.

## Problem Or Opportunity

Re-creating similar nodes by hand is slow and error-prone.

## Scope

### In Scope

- Mod+C / Mod+X / Mod+V and Mod+D through the TASK-0023 registry; paste at the cursor with new ids
- Internal edges are kept, dangling ones dropped; Start/End are never duplicated
- Clipboard payload is versioned JSON so pasting into another workflow works; credential references are kept only if the user owns them

### Out Of Scope

- Pasting arbitrary external JSON as nodes

## Stakeholders Or Users

- Workflow authors using the LangGraph Studio editor

## Current Context

- React Flow editor (`frontend/src/pages/Editor.tsx`), shadcn/Tailwind UI, en/vi i18n

## Desired Behavior

Copy/cut/paste and duplicate selected nodes (with the edges between them), also across workflows.

## Business Rules

- Strict shadcn (tokens only), en/vi texts, keyboard and screen-reader accessible

## Constraints

- Mock/offline mode must keep working without API keys.

## Acceptance Criteria

- Copy → paste duplicates nodes and their internal edges with fresh ids
- Paste into another workflow works
- Each paste is one undo step (TASK-0024)

## Open Questions

- None yet

## Related Artifacts

- Delivered by `.factory-state/tasks/done/TASK-0026-copy-paste-and-duplicate-nodes.md`, merged to `develop`.
