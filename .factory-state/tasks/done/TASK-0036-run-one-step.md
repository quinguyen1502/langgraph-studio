# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0036
- Status: done
- Phase: run one step
- Owner: Thái Quí Nguyễn
- Created: 2026-10-18
- Updated: 2026-10-18
- Requirement IDs: REQ-0024
- Design IDs:
- Architecture IDs: ARCH-0001

## Objective

Let the author execute one superstep, pause, then step again or continue.

## Scope

### In Scope

- A one-superstep limit on the studio run path, a pause after a chosen node finishes, a pause event and status that are not Human `waiting`, and resume of that same run for one more step, until another node, or for the rest of the graph
- Editor Step and Continue controls, history, and the trace reading the new pause without opening the approval panel

### Out Of Scope

- Editing state between steps
- Stepping an imported repository graph
- `Command`, `Send`, `error_handler`, and `defer`

## Inputs

- `.factory-state/artifacts/REQ-0024-run-one-step.md`

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0024-run-one-step.md`
- Review: `.factory-state/artifacts/REV-0035-task-0036.md`
- QA: `.factory-state/artifacts/QA-0035-task-0036.md`
- Architecture: `.factory-state/artifacts/ARCH-0001-current-architecture.md`
- Runtime: `backend/app/engine/runtime.py`
- Run service: `backend/app/services/run_service.py`
- Socket: `backend/app/api/routes/runs_ws.py`
- Editor: `frontend/src/pages/Editor.tsx`
- Trace: `frontend/src/lib/trace.ts`

## Expected Outputs

- A paused one-step run covered by a backend test
- Step and Continue on the editor
- One sentence in `README.md` and `README.vi.md` for the step control

## Implementation Notes

- Stop after one superstep using the checkpoint `run_stream` already yields. Do not pass `timeout=` to `add_node`.
- Name the client event `run_paused` and the stored status `paused`. Keep `run_waiting` / `waiting` for Human approval only, so pending approvals and approval notifications do not fire.
- Resume without a human `value`, on the same run id. A follow-up message carries the one-step limit; Continue omits it.
- The socket may close on pause the way it closes on `run_waiting`. The editor appends the next segment to the same log.
- Parallel nodes in the superstep all finish before the pause.
- Add `status.paused` and the button labels to `frontend/src/locales/en.json` and `vi.json`.

## Constraints

- Routers call services. Services call the engine. No FastAPI imports in the engine.
- New error codes, if any, go in `core/errors.py` `CATALOG`, `docs/api-errors.md`, and both locale files.
- shadcn components and theme tokens. No hard-coded colours.
- Branch `factory/task-0036-run-one-step` from `develop`. One Draft PR into `develop`. Do not merge until the owner asks.
- Pytest uses `/tmp/lgs-qa-venv`. Do not use `backend/.venv`. Frontend typecheck is `cd frontend && npx tsc -b`.

## Dependencies

- None. Independent of TASK-0037. Start from `develop`.

## Acceptance Criteria

- Same as REQ-0024.

## Validation Plan

- `cd backend && /tmp/lgs-qa-venv/bin/python -m pytest -q tests/test_node_policy.py tests/test_layers.py` plus the run or runtime test that covers one step, a second step, continue, and a parallel superstep
- `cd frontend && npx tsc -b`
- `git diff --check`
- In the browser, Step a linear graph, confirm one node finishes and the approval panel stays hidden, then Continue

## Assumptions

- Small-task workflow. Designer and architect are skipped; REQ-0024 records the experience and the checkpoint resume path.
- `factory ready` does not exit 0 here. The owner asked for the task anyway. Do not install packages to clear that check.
- GitHub Actions on this private repo fails in about two seconds because the quota is spent. Local tests are the evidence. Do not treat a red Actions run as a product failure, and do not change billing.

## Open Questions

- None

## Activity Log

- 2026-10-18: Owner asked for the task. REQ-0024 approved with the one-superstep reading. Task filed in `todo`. Not started.
- 2026-10-18: Owner said to start TASK-0036. Branch `factory/task-0036-run-one-step` from `develop` at `842caa3`. Moved to `doing`. No source edited.
- 2026-10-18: Owner said to implement. One working superstep pauses as `run_paused` / `paused`. Start does not consume the step. Step and Continue are on the editor.
- 2026-10-18: Owner asked to commit and open a PR. Moved to `review`. Draft PR #39 into `develop`: https://github.com/quinguyen1502/langgraph-studio/pull/39
- 2026-10-18: Owner asked to choose a node and run from Start until that node finishes. Run to here added on the same PR.
- 2026-10-18: Owner said the behaviour was fine and asked to finish the remaining steps. REV-0035 has no blocking findings. QA-0035 passed. Task set to done. PR #39 marked Ready. Not merged.

## Handoff Notes

- Ready PR #39 into `develop`: https://github.com/quinguyen1502/langgraph-studio/pull/39
- Do not merge until the owner asks.
- Do not stack TASK-0037 on this branch.
