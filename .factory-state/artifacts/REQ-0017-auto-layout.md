# Requirement

## Metadata

- Project: langgraph-studio
- Requirement ID: REQ-0017
- Status: Proposed
- Owner: Thái Quí Nguyễn
- Created: 2026-10-17
- Updated: 2026-10-17
- Source: owner request 2026-10-17 (Phase 5: Editor UX) — suggested by the factory agent, approved by the owner 2026-10-17

## Summary

One-click automatic layout of the graph (left-to-right or top-to-bottom).

## Problem Or Opportunity

Imported or grown workflows get messy; arranging nodes by hand takes time.

## Scope

### In Scope

- Layout action (toolbar + shortcut) using a layered graph layout (e.g. dagre/elkjs), direction LR/TB
- Respects node sizes, keeps Start first / End last, handles loops and parallel branches
- Result is one undo step and is saved like any move

### Out Of Scope

- Live/continuous layout while editing

## Stakeholders Or Users

- Workflow authors using the LangGraph Studio editor

## Current Context

- React Flow editor (`frontend/src/pages/Editor.tsx`), shadcn/Tailwind UI, en/vi i18n

## Desired Behavior

One-click automatic layout of the graph (left-to-right or top-to-bottom).

## Business Rules

- Strict shadcn (tokens only), en/vi texts, keyboard and screen-reader accessible

## Constraints

- Mock/offline mode must keep working without API keys.

## Acceptance Criteria

- Layout produces no overlapping nodes on the seeded examples
- Undo restores the previous positions
- Works for imported workflows

## Open Questions

- None yet
