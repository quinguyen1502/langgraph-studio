# Requirement

## Metadata

- Project: langgraph-studio
- Requirement ID: REQ-0018
- Status: Proposed
- Owner: Thái Quí Nguyễn
- Created: 2026-10-17
- Updated: 2026-10-17
- Source: owner request 2026-10-17 (Phase 5: Editor UX) — suggested by the factory agent, approved by the owner 2026-10-17

## Summary

A Mod+K command palette to search actions, nodes and workflows.

## Problem Or Opportunity

Actions are spread over toolbars, menus and dialogs; there is no quick keyboard way to reach them.

## Scope

### In Scope

- shadcn Command dialog (Mod+K) listing registry actions (TASK-0023), add-node by type, jump to node, open workflow, open settings pages
- Fuzzy search, en/vi labels, shows each action's shortcut

### Out Of Scope

- Plugin-provided commands

## Stakeholders Or Users

- Workflow authors using the LangGraph Studio editor

## Current Context

- React Flow editor (`frontend/src/pages/Editor.tsx`), shadcn/Tailwind UI, en/vi i18n

## Desired Behavior

A Mod+K command palette to search actions, nodes and workflows.

## Business Rules

- Strict shadcn (tokens only), en/vi texts, keyboard and screen-reader accessible

## Constraints

- Mock/offline mode must keep working without API keys.

## Acceptance Criteria

- Mod+K opens the palette anywhere in the app; Enter runs the highlighted action
- Adding a node from the palette places it in view and selects it
- e2e covers open, search and run

## Open Questions

- None yet
