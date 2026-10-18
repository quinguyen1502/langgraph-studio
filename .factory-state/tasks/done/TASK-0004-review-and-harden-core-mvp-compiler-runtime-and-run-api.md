# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0004
- Status: done
- Owner: Grok Bot (agent)
- Priority: Phase 1 Feasibility, step 4 — after TASK-0003 (auth/list hardening), before TASK-0005 (real LLM providers)
- Previous ID: TASK-0014 (renumbered 2026-10-16, DEC-0007)
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

- Repo import hardening and container sandboxing (TASK-0015, Phase 4)
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
- Related tasks: TASK-0002 (CI, PR #1), TASK-0003 (auth/list hardening), TASK-0005 (LLM providers, PR #2 — old TASK-0003), TASK-0015 (repo import + sandbox, last phase)

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

- Builds on TASK-0002 (pyproject/CI). Independent of TASK-0005; if TASK-0005 (PR #2) merges first, also cover provider-call errors

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
- SQLite remains the store until TASK-0009

## Open Questions

- Resolved (owner, 2026-10-16): recursion limit 25 (reuse `STUDIO_RECURSION_LIMIT` from TASK-0016), run timeout 120 s, 256 KB per event, 2 MB per stored run.
- Open: should the recursion limit be per-workflow configurable? (not done)

## Activity Log

- 2026-10-16: Created as TASK-0014 (plan only, PR #3); renumbered to TASK-0004 (DEC-0007).
- 2026-10-16: Owner approved implementation with defaults. Moved todo -> doing on `factory/task-0004-review-and-harden-core-mvp`, based on the TASK-0016 branch (PR #6). Implementation goes in a new draft PR (#7); the plan PR #3 remains the record of the plan.
- 2026-10-16: Coverage baseline (TASK-0016 branch, 35 tests): statements 92% (636 stmts, 48 missed), branches+statements 89%.
- 2026-10-16: Implemented. The audit findings are in REV-0005-task-0004. Coverage after (60 tests): statements 94% (819, 51 missed), branches+statements 91%.
- 2026-10-16: Moved doing -> review. QA-0005-task-0004 records the results; the manual real-provider E2E is pending for the owner.

- 2026-10-17: Status set to done to match the done/ folder. Previous Status was `todo`. Review REV-0005. QA QA-0005.

## Handoff Notes

- Branch `factory/task-0004-review-and-harden-core-mvp`; PR base `factory/task-0016-run-trace-timeline-ui` (#6). Merge order: #4 → #1 → #3 → #5 → #6 → #7 → #2.
- New env vars: `STUDIO_RUN_TIMEOUT`, `STUDIO_EVENT_MAX_BYTES`, `STUDIO_RUN_MAX_BYTES`, `STUDIO_INPUT_MAX_BYTES`, `STUDIO_WORKFLOW_MAX_BYTES`, `STUDIO_ENABLE_DEMO_TOOLS` (README).
- When TASK-0005 (#2) merges, provider-call errors go through `safe_error` too; check the redaction against real provider messages.

- Use branch `factory/task-0004-review-and-harden-core-mvp` when implementation begins. (Planning PR #3 used branch `factory/task-0014-plan-mvp-hardening`.)
