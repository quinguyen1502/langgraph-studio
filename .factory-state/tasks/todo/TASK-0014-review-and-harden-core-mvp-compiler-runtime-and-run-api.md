# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0014
- Status: todo
- Owner:
- Priority: P0 — after TASK-0002/TASK-0003, before TASK-0004
- Created: 2026-10-16
- Updated: 2026-10-16
- Requirement IDs: REQ-0001
- Design IDs:
- Architecture IDs: ARCH-0001

## Objective

Review and harden the core MVP (REQ-0001): audit the validator, compiler and run runtime for edge cases, make every failure surface as a clear `error` event instead of a hang or crash, support cancel/timeout/concurrent runs safely, validate API input, and close test-coverage gaps. Document a manual end-to-end check with a real LLM provider.

## Scope

### In Scope

- Graph validation edge cases: cycles/loops (allowed only through a Condition node, guarded by LangGraph `recursion_limit` with a configurable default), unreachable and dangling nodes, edges to deleted nodes, duplicate node/edge ids, multiple Start/End, self-loops on non-Condition nodes
- Condition routing: default branch, no-match without default (clear error), case/whitespace handling, non-string field values
- State: empty state schema, fields missing in input, type mismatches against the schema, large state/deltas (size cap on events and stored run history)
- Error handling: LLM/Tool/HTTP exceptions → `error` event naming node + message (no stack traces or secrets), run status `error` stored in history
- WebSocket lifecycle: client disconnect stops the run (cooperative cancel), explicit `{"type":"cancel"}` message, run status `cancelled`
- Run timeout: per-run wall-clock limit (`STUDIO_RUN_TIMEOUT`), status `timeout`
- Concurrency: several simultaneous runs (same/different users) do not mix events or state; SQLite writes safe under concurrency
- Input validation: workflow JSON schema (pydantic models for nodes/edges/state), run input must be a JSON object, size limits on workflow and input, clear 422/400 messages
- Test coverage: add pytest cases for all of the above; measure coverage (`pytest --cov`) and record baseline/after
- Manual E2E with a real provider: documented step (README + QA artifact) for the owner to run with their own key

### Out Of Scope

- Container sandboxing of imports (TASK-0004)
- New node types, versioning, HITL, RBAC
- Frontend redesign (only small UI changes needed to show cancel/timeout states)

## Inputs

- `.factory-state/artifacts/REQ-0001-mvp-baseline.md`
- `.factory-state/artifacts/ARCH-0001-current-architecture.md`
- `backend/app/compiler.py`, `backend/app/main.py`, `backend/tests/`
- `frontend/src/pages/Editor.tsx` (run panel)

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0001-mvp-baseline.md`
- Architecture: `.factory-state/artifacts/ARCH-0001-current-architecture.md`
- Discovery: `.factory-state/artifacts/DISC-0001-project-context.md`
- Related tasks: TASK-0002 (CI, PR #1), TASK-0003 (LLM providers, PR #2), TASK-0004 (sandboxed imports, next after this)

## Expected Outputs

- Hardened validator/compiler/runtime and WebSocket handler
- New/updated pytest suites and a coverage report recorded in the task
- Audit findings list (fixed vs. deferred) in the task Activity Log or a review artifact
- README section "Manual E2E with a real provider"
- REV and QA artifacts

## Constraints

- Keep the event protocol backward compatible (`node_started`, `node_finished`, `run_finished`, `error`); new statuses are additive (`cancelled`, `timeout`)
- Mock mode and existing tests must keep passing
- No real API keys in the repository or CI

## Dependencies

- Builds on TASK-0002 (pyproject/CI) and TASK-0003 (provider calls); start from `main` after they merge, or stack on the TASK-0003 branch and document it

## Acceptance Criteria

- Validator rejects with a clear message: dangling edges, unreachable nodes, duplicate ids, multiple Start, self-loops on non-Condition nodes, cycles without a Condition node
- A loop through a Condition node that never exits ends with an `error` event mentioning the recursion limit (no hang); limit is configurable
- Condition with no matching label and no default produces an `error` event naming the node and the value; with a default it routes to the default
- Runs with empty state schema and with input missing schema fields complete or fail with clear messages (no 500)
- Events and stored run history are capped for large state (configurable), with truncation marked
- Closing the WebSocket mid-run stops the run within a few seconds and records status `cancelled`; a `cancel` message does the same
- A run exceeding `STUDIO_RUN_TIMEOUT` stops with status `timeout` and an `error` event
- At least 5 concurrent runs complete with correct, non-interleaved events per connection (test)
- Invalid workflow JSON and non-object/oversized run input return 400/422 with readable messages
- Backend coverage measured before and after; new tests cover every criterion above
- README documents the manual real-provider E2E; QA artifact records whether the owner ran it

## Validation Plan

- `cd backend && .venv/bin/python -m pytest -q` (plus `pytest --cov=app` before/after)
- `cd frontend && npm run build && npm run lint`
- `factory verify run --profile full`, `factory validate`
- GitHub Actions green on the PR (once account billing is resolved)
- Manual: run the seeded example with a real OpenAI/Anthropic credential (owner)

## Assumptions

- Cooperative cancellation between LangGraph supersteps is acceptable (an in-flight HTTP call may finish before the run stops)
- SQLite remains the store until TASK-0008

## Open Questions

- Default recursion limit (LangGraph default 25) and run timeout (proposed 120s) acceptable?
- Size caps: proposed 256 KB per event delta, 2 MB per stored run

## Activity Log

- 2026-10-16: Created task (owner-approved scope proposal); placed in todo as next P0 before TASK-0004. Not started.

## Handoff Notes

- Use branch `factory/task-0014-review-and-harden-core-mvp` when implementation begins.
