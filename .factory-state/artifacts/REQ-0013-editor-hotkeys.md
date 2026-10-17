# Requirement

## Metadata

- Project: langgraph-studio
- Requirement ID: REQ-0013
- Status: Proposed
- Owner: Thái Quí Nguyễn
- Created: 2026-10-17
- Updated: 2026-10-17
- Source: owner request 2026-10-17 (Phase 5: Editor UX)

## Summary

Keyboard shortcuts for the workflow editor and a cheatsheet dialog that lists them.

## Problem Or Opportunity

Editing a workflow is mouse-only today (save, run, delete a node, zoom all need clicks).

## Scope

### In Scope

- A single shortcut registry (id, keys per platform: Ctrl on Windows/Linux, ⌘ on macOS, label key, handler) used by the editor and the cheatsheet
- Shortcuts: save (Mod+S), run (Mod+Enter), stop run, delete selection (Delete/Backspace), select all (Mod+A), fit view (Shift+1), zoom in/out, close panel (Esc), open cheatsheet (? or Mod+/)
- Shortcuts are ignored while typing in an input, textarea, select or code editor
- Cheatsheet: shadcn Dialog grouped by category (General, Canvas, Run), en/vi labels, shown keys match the platform

### Out Of Scope

- User-defined remapping
- Shortcuts outside the editor

## Stakeholders Or Users

- Workflow authors using the LangGraph Studio editor

## Current Context

- React Flow editor (`frontend/src/pages/Editor.tsx`), shadcn/Tailwind UI, en/vi i18n

## Desired Behavior

Keyboard shortcuts for the workflow editor and a cheatsheet dialog that lists them.

## Business Rules

- Strict shadcn (tokens only), en/vi texts, keyboard and screen-reader accessible

## Constraints

- Mock/offline mode must keep working without API keys.

## Acceptance Criteria

- Mod+S saves without the browser's save-page dialog; Mod+Enter starts a run
- Delete removes the selected nodes/edges (except Start/End) and is ignored inside text fields
- ? opens the cheatsheet; every registered shortcut appears there with en/vi labels
- e2e covers save, delete and the cheatsheet

## Open Questions

- None yet
