# Task

## Metadata

- Project: superstep
- Task ID: TASK-0078
- Status: review (draft PR)
- Owner: Thái Quí Nguyễn
- Created: 2026-10-23
- Updated: 2026-10-23
- Requirement IDs: REQ-0045
- Design IDs: none
- Architecture IDs: DEC-0008

## Objective

Apply the approved Vietnamese glossary to the UI, README and handbook, and guard it with a locale test.

## Scope

### In Scope

- `docs/ui-conventions.md` rule 10 (glossary) and checklist line.
- `frontend/src/locales/vi.json`: High fixes (`trace.empty`, `trace.done`, run/node terms), glossary pass, tone
  marks, untranslated labels, wording, shorter long help strings; `list.untitled` (en, vi).
- `components/ui/dialog.tsx` "Close" x2 and `pages/Workflows.tsx` default name through i18n.
- `src/lib/__tests__/locales.test.ts`.
- `README.md`, `README.vi.md`; `handbook/docs/vi/**`.
- e2e specs that assert changed vi strings.

### Out Of Scope

- Archive tags and branch pruning (owner: skip).

## Validation Plan

- `npm test`, `npm run lint`, `npm run build`, `npx playwright test` (E2E_CODE_RUNTIME=subprocess; no Docker on the
  box), `zensical build --strict` (en, vi), `check_images.py site`; vi screenshots at 1280 and 1024 px.

## Activity Log

- 2026-10-23: review written; owner approved the glossary and fix plan steps 1-8 (skip step 9).
- 2026-10-23: implemented on `factory/task-0078-vi-locale-polish`; draft PR into develop.

## Handoff Notes

- Not merged; needs owner review.
