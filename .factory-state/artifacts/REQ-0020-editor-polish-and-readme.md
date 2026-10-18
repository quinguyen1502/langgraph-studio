# Requirement

## Metadata

- Project: langgraph-studio
- Requirement ID: REQ-0020
- Status: Implemented
- Owner: Thái Quí Nguyễn
- Created: 2026-10-18
- Updated: 2026-10-18
- Source: owner requests on 2026-10-18 (README en/vi, editor layout fixes, JSON editor, skeletons, empty-state actions, canvas context menu). Recorded after the work was already in the working tree.

## Summary

Polish the editor the owner was testing, and replace the task-diary README with a short English page plus a Vietnamese twin.

## Problem Or Opportunity

The owner hit several editor defects while testing, and the README still read like a task diary, including a stale import-checkpoint sentence.

## Scope

### In Scope

- `README.md` in English and `README.vi.md` in Vietnamese. Each page links to the other. English is the GitHub default.
- Save and Run: icon and label share one line, in the center of the header. No header divider.
- No left colour bar on a node. The type icon keeps the type colour. The run-status outline stays. Locking the canvas keeps the selected node selected. The lock control is the filled padlock, in proportion with the other control buttons.
- The more-actions tooltip stays closed after the menu closes. The browser title is LangGraph Studio. The favicon is the workflow mark.
- CodeMirror for the run input and the Workflow JSON dialog, with JSON syntax colours and a fold icon that sits on the line. The dialog does not overflow.
- Skeleton placeholders for the editor, the workflow table, settings lists, and the template gallery while the first load has no data. Button spinners stay.
- Empty-state links or actions for knowledge, MCP, subgraph, LLM credential, and approval channel.
- Right-click on a node or edge: insert before, insert after, insert on that edge, copy, cut, duplicate, delete. Start and End cannot be copied or deleted. A node with more than one incoming edge hides Insert before. A node with more than one outgoing edge hides Insert after. Delete from the config panel is removed. The Delete key still works.

### Out Of Scope

- Changing how the app picks the first language. `fallbackLng` stays `en`.
- Per-node retry, timeout, and cache (REQ-0019, already merged).
- A new backend API.

## Stakeholders Or Users

- Workflow authors using the editor
- Someone reading the repo on GitHub

## Current Context

- Editor: `frontend/src/pages/Editor.tsx`, shadcn, xyflow, en/vi locales
- Import behaviour in the README must match the merged Docker sandbox (REQ-0009)

## Desired Behavior

- The README describes the product, not task numbers. The import section says a Docker run starts a new container, and `STUDIO_IMPORT_RUNTIME=subprocess` starts a new subprocess.
- The listed editor defects are gone, and the new actions are available in both languages.

## Business Rules

- UI strings live in `en.json` and `vi.json` with the same keys.
- Theme tokens only. Syntax colours are `--syntax-key` and `--syntax-string`. Numbers stay on `info`, booleans on `warning`.
- Delete from the canvas menu is still a plain delete. Typed-name confirmation stays on workflow and settings deletes.

## Constraints

- shadcn/ui. No hard-coded palette colours.
- CodeMirror is installed inside `frontend/`. The lockfile keeps `libc` filters on optional native packages.

## Acceptance Criteria

- `README.md` is English and links to `README.vi.md`, and the Vietnamese page links back.
- Save and Run text sits on the icon. The name and those controls sit in the center of the header. There is no header divider.
- A node has no left colour bar. Run status still uses the card outline. A selected node keeps its ring when the canvas is locked. The lock button shows a closed or open padlock at the control-button proportion.
- Choosing an item in More actions does not leave the tooltip open. The document title is LangGraph Studio. The favicon is the workflow mark.
- Run input and Workflow JSON use the JSON editor. Keys, strings, numbers, and booleans are different colours. A long line wraps.
- First load of the workflow list, editor, and settings lists shows skeletons instead of a blank or a lone spinner.
- Empty knowledge, MCP, subgraph, credential, and approval-channel states offer a link or action.
- Right-click inserts a node before or after when the node has a single neighbour on that side, and inserts on a specific edge. Copy, cut, duplicate, and delete are on the menu. Start has no delete.

## Edge Cases

- Read-only and imported graphs do not open the edit menu.
- Pane right-click does not open the browser menu or an empty studio menu.
- Insert on a branch keeps the existing edge label on the first half of the splice.

## Assumptions

- The owner already directed each change while testing, including later corrections on PR #35: drop the header divider, drop the left colour bar, keep the run-status outline, suppress the more-actions tooltip after the menu closes, use the app favicon and title, and keep the lock icon in proportion. No separate design artifact.
- One task, because the changes are already one working tree and the owner asked to finish that tree.
- `factory ready` does not exit 0 on this machine (no PyYAML on system Python, no `textual` in the QA venv). The owner asked to finish the uncommitted work anyway.

## Open Questions

- None

## Related Artifacts

- `.factory-state/artifacts/ARCH-0001-current-architecture.md`
- `.factory-state/tasks/done/TASK-0032-editor-polish-and-readme.md`
- `.factory-state/artifacts/REV-0031-task-0032.md`
- `.factory-state/artifacts/QA-0031-task-0032.md`
- `docs/ui-conventions.md`
