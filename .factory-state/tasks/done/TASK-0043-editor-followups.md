# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0043
- Status: done
- Phase: editor maintenance
- Owner: Thái Quí Nguyễn
- Created: 2026-10-18
- Updated: 2026-10-18
- Requirement IDs: REQ-0030
- Design IDs:
- Architecture IDs:

## Objective

Give focus back to the template editor as soon as a field is picked, and split the vendor libraries into their own chunks.

## Scope

### In Scope

- `frontend/src/components/template-editor.tsx`, `frontend/e2e/template-editor.spec.ts`
- `frontend/vite.config.ts`

### Out Of Scope

- Library changes

## Inputs

- `.factory-state/artifacts/REQ-0030-editor-followups.md`

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0030-editor-followups.md`
- Review: `.factory-state/artifacts/REV-0041-task-0043.md`
- QA: `.factory-state/artifacts/QA-0041-task-0043.md`

## Constraints

- Branch from `develop` (`4ee1ccd`). One PR into `develop`. Do not merge until the owner asks.

## Dependencies

- TASK-0041 (PR #44), merged.

## Acceptance Criteria

- Same as REQ-0030.

## Validation Plan

- `cd frontend && npx tsc -b && npx vitest run && npx oxlint && npx vite build`
- `cd frontend && PW_CHROME=... E2E_UVICORN=../backend/.venv/bin/uvicorn npx playwright test`
- `git diff --check`

## Assumptions

- `factory ready` does not exit 0 here (the CLI needs `textual`). GitHub Actions does not run (billing). Local checks are the evidence.

## Open Questions

- None

## Activity Log

- 2026-10-18: Filed from items 9 and 11 of the remaining-work report; the owner asked to do them. The insert menu is no longer modal and the editor takes focus when a field is picked; the spec now types straight after picking and fails on the old code ("Hi message ghost answerreply" without the typed `Z`). Vendor chunks: react 259 kB, codemirror 423 kB, flow 178 kB, ui 205 kB, i18n 66 kB; Editor 180 kB and index 213 kB (were 827 kB and 695 kB). REV-0041 has no blocking findings. QA-0041 passed. Task set to done. PR into `develop`. Not merged.

## Handoff Notes

- None.
