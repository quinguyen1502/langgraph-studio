# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0050
- Status: done
- Phase: engine
- Owner: Thái Quí Nguyễn
- Created: 2026-10-19
- Updated: 2026-10-19
- Requirement IDs: REQ-0036
- Design IDs: DEC-0039
- Architecture IDs: DEC-0032, DEC-0018, DEC-0009

## Objective

A Decision node backed by TypeSafe's Jev.

## Scope

### In Scope

- Backend: `engine/decisions.py`, `engine/providers.py` (`TypeSafe`, `kind`), `engine/validator.py` (rules, `written()`), `engine/nodes.py`, `engine/effects.py`, `engine/node_policy.py`, `engine/usage.py` (`jev` price)
- Frontend: `components/decision-settings.tsx`, `components/editor/{meta.ts,editor-config.tsx}`, `components/template-preview.tsx`, `lib/providers.ts`, `index.css` (`--node-decision*`), locales
- Tests: `backend/tests/test_decisions.py`, `frontend/e2e/decision.spec.ts`
- Docs: both READMEs, `.env.example`; roadmap also marks TASK-0049 merged (PR #54)

### Out Of Scope

- `box` questions, images, compression, the TypeSafe SDK

## Inputs

- `.factory-state/artifacts/REQ-0036-jev-decision-node.md`
- https://docs.typesafe.ai (Quick Start, API reference, Score), read 2026-10-19

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0036-jev-decision-node.md`
- Decision: `.factory-state/decisions/DEC-0039-jev-decision-node.md`
- Review: `.factory-state/artifacts/REV-0047-task-0050.md`
- QA: `.factory-state/artifacts/QA-0047-task-0050.md`

## Constraints

- Do not merge until the owner asks.

## Dependencies

- None (branched from develop at `4d6b130`).

## Acceptance Criteria

- Same as REQ-0036.

## Validation Plan

- `cd backend && .venv/bin/python -m pytest -q`
- `cd frontend && npx tsc -b && npx vitest run && npx oxlint && npx vite build`
- `cd frontend && PW_CHROME=… E2E_UVICORN=../backend/.venv/bin/uvicorn npx playwright test`
- `git diff --check`

## Assumptions

- No TypeSafe key is available here (early access). Tests use a mocked HTTP transport shaped from the docs.
- `factory ready` does not exit 0 here (the CLI needs `textual`). GitHub Actions does not run (billing). Local checks are the evidence.

## Open Questions

- None

## Activity Log

- 2026-10-19: The owner asked about Jev and then said to start. The app refused to start a separate session from that turn, so the work was done in this session (the proposal card was withdrawn). Found by eye on the dev app: the long "None (…)" credential label widened the config panel past its edge; shortened to "None", and the hint below explains the fallbacks.
