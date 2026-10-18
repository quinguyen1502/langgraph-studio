# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0032
- Status: done
- Phase: editor polish
- Owner:
- Created: 2026-10-18
- Updated: 2026-10-18
- Requirement IDs: REQ-0020
- Design IDs:
- Architecture IDs: ARCH-0001

## Objective

Record and ship the uncommitted editor polish and bilingual README as REQ-0020.

## Scope

### In Scope

- English and Vietnamese READMEs
- Header divider, Save/Run alignment, node accent radius
- CodeMirror JSON editor, syntax tokens, fold icon
- Skeleton loading for first-load lists and the editor
- Empty-state links and actions
- Canvas context menu, including insert before, insert after, and insert on an edge

### Out Of Scope

- App language detection
- REQ-0019 execution settings
- Backend API changes

## Inputs

- `.factory-state/artifacts/REQ-0020-editor-polish-and-readme.md`
- `.factory-state/artifacts/ARCH-0001-current-architecture.md`

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0020-editor-polish-and-readme.md`
- Architecture: `.factory-state/artifacts/ARCH-0001-current-architecture.md`
- Review: `.factory-state/artifacts/REV-0031-task-0032.md`
- QA: `.factory-state/artifacts/QA-0031-task-0032.md`

## Expected Outputs

- `README.md`, `README.vi.md`, the editor polish files, and the CodeMirror lockfile entries
- `libc` filters stay on optional native packages

## Implementation Notes

- The work was written on `develop` before this task existed. The commit moves that working tree onto the task branch.
- `leading-none` loses to a later `text-*` utility. The button uses `leading-none!`. The `sm` icon nudge is `translate-y-[-0.5px]`, which sets the CSS `translate` property.
- Separator orientation uses `data-[orientation=...]`. Radix does not set `data-vertical`.

## Constraints

- shadcn/ui, theme tokens, en/vi keys. Lockfile must not strip `libc` from optional native packages.

## Dependencies

- TASK-0031 is merged. This branch starts from that `develop`.

## Acceptance Criteria

- Same as REQ-0020.

## Validation Plan

- `cd frontend && npx tsc -b`
- `cd frontend && npm run build`
- `git diff --check`

## Assumptions

- Designer and architect skipped. The owner specified each fix while testing.
- `factory ready` failed locally for missing PyYAML and `textual`. The owner asked to finish this working tree anyway.
- Draft PR into `develop` was the review step. The owner asked to finish and merge on 2026-10-18.

## Open Questions

- None

## Activity Log

- 2026-10-18: Owner asked to finish the uncommitted editor and README work.
- 2026-10-18: REQ-0020 approved from those earlier requests. Task opened on `factory/task-0032-editor-polish-and-readme`.
- 2026-10-18: `npx tsc -b` and `npm run build` passed. `git diff --check` was clean. Locale keys match. Lockfile adds CodeMirror and keeps `libc`.
- 2026-10-18: Moved to review. Draft PR #35 opened into `develop`: https://github.com/quinguyen1502/langgraph-studio/pull/35
- 2026-10-18: Owner follow-up on the PR: center the name and run controls and drop the header divider; drop the left colour bar on nodes (the type icon keeps that colour; the run-status outline stays); keep the more-actions tooltip closed after the menu closes; favicon matches the app mark.
- 2026-10-18: Page title set to LangGraph Studio. Lock control uses the filled padlock and a square viewBox so the 12×12 control CSS does not squash it.
- 2026-10-18: Owner asked to finish and merge. REV-0031 has no blocking findings. QA-0031 passed (`tsc -b`, `npm run build`, `git diff --check`). Task set to done.

## Handoff Notes

- Do not include REQ-0019 files. They are already on `develop`.
- Keep `libc` in the lockfile.
- Branch `factory/task-0032-editor-polish-and-readme`. PR #35. Owner asked to merge.
