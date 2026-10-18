# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0034
- Status: done
- Phase: editor leftovers
- Owner:
- Created: 2026-10-18
- Updated: 2026-10-18
- Requirement IDs: REQ-0022
- Design IDs:
- Architecture IDs: ARCH-0001

## Objective

Translate the JSON fold tooltip, test `spliceNode`, and fix the accent-stripe example.

## Scope

### In Scope

- Fold marker titles in both locales
- `spliceNode` unit tests
- One example line in `docs/ui-conventions.md`

### Out Of Scope

- Context-menu visibility rules
- TASK-0033 record edits, except that this branch contains them so the roadmap can append

## Inputs

- `.factory-state/artifacts/REQ-0022-editor-leftovers.md`
- `.factory-state/artifacts/QA-0031-task-0032.md`

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0022-editor-leftovers.md`
- Review: `.factory-state/artifacts/REV-0033-task-0034.md`
- QA: `.factory-state/artifacts/QA-0033-task-0034.md`

## Expected Outputs

- Locale keys, tests, and the conventions line

## Implementation Notes

- `foldIcon` builds a DOM node, so it calls `i18n.t` instead of `useTranslation`.
- Stacked on `factory/task-0033-align-delivery-records`. Merge PR #36 first.

## Constraints

- Same keys in `en.json` and `vi.json`.

## Dependencies

- TASK-0033 is the branch base. It does not need to be merged for these tests to run.

## Acceptance Criteria

- Same as REQ-0022.

## Validation Plan

- `cd frontend && npm test`
- `cd frontend && npx tsc -b`
- `git diff --check`

## Assumptions

- `factory ready` did not exit 0 here. The owner asked to proceed with the leftover plan anyway.

## Open Questions

- None

## Activity Log

- 2026-10-18: Owner approved the leftover plan. REQ-0022 opened. Task started on `factory/task-0034-editor-leftovers`, based on TASK-0033.
- 2026-10-18: `npm test` for `graph-ops.test.ts` passed (8). `npx tsc -b` passed. Fold titles checked in Chrome for en and vi. Moved to review. Draft PR #37 opened into `develop`: https://github.com/quinguyen1502/langgraph-studio/pull/37
- 2026-10-18: Rebased onto `develop` after PR #36 merged. Owner asked to finish and merge. REV-0033 has no blocking findings. QA-0033 passed. Task set to done.

## Handoff Notes

- Draft PR into `develop`. Do not merge until the owner asks. Merge PR #36 first.
