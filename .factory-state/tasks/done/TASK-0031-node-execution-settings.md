# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0031
- Status: done
- Phase: node execution settings
- Owner:
- Created: 2026-10-18
- Updated: 2026-10-18
- Requirement IDs: REQ-0019
- Design IDs:
- Architecture IDs: ARCH-0001

## Objective

Implement REQ-0019: per-node retry, timeout, and cache on the canvas.

## Scope

### In Scope

- Execution fields for LLM, Retriever, Tool, MCP, and Human
- `RetryPolicy` and `CachePolicy` passed to `add_node`
- A timeout cap that stops the attempt and stays retryable
- Validator messages and engine tests

### Out Of Scope

- Start, End, Condition, Join, Subgraph, and imported code nodes
- `error_handler`, `defer`, per-node input schema, `Command`, and `Send`
- Cache shared across runs
- The other uncommitted editor work (README, context menu, JSON editor, skeletons, empty-state links)

## Inputs

- `.factory-state/artifacts/REQ-0019-node-execution-settings.md`
- `.factory-state/artifacts/ARCH-0001-current-architecture.md`

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0019-node-execution-settings.md`
- Architecture: `.factory-state/artifacts/ARCH-0001-current-architecture.md`
- Review: `.factory-state/artifacts/REV-0030-task-0031.md`
- QA: `.factory-state/artifacts/QA-0030-task-0031.md`

## Expected Outputs

- `backend/app/engine/node_policy.py`
- Compiler and validator wiring
- `frontend/src/components/node-runtime.tsx` and the config panel hookup
- en/vi strings
- `backend/tests/test_node_policy.py`

## Implementation Notes

- LangGraph 1.2.16 rejects `add_node(..., timeout=)` on a sync node. The node body runs on a daemon thread and the attempt raises `NodeTimeoutError` after the cap. The thread may still finish later.
- Retry uses `backoff_factor=1` and `jitter=False`, so the wait is the number entered. A missing wait uses 0.5 seconds.
- `Interrupt` is excluded from retry.
- Cache is an `InMemoryCache` created for that compile only.

## Constraints

- shadcn/ui and theme tokens. Strings in both locale files. No FastAPI in the engine.

## Dependencies

- None. Phases 1–5 and TASK-0030 are done on `develop`.

## Acceptance Criteria

- The Execution section is on LLM, Retriever, Tool, MCP, and Human, and absent on Start
- Values survive selecting another node and coming back
- Connection-error retry, same-input cache, timeout-plus-retry, and a Human pause are covered by `tests/test_node_policy.py`
- Out-of-range values fail validation with a message that names the node

## Validation Plan

- `cd backend && /tmp/lgs-qa-venv/bin/python -m pytest -q tests/test_node_policy.py tests/test_compiler.py tests/test_core_hardening.py`
- `cd frontend && npx tsc -b`

## Assumptions

- Designer skipped: the fields sit in the existing config panel.
- `factory ready` did not exit 0 here. System `python3` has no PyYAML. `/tmp/lgs-qa-venv` has PyYAML but no `textual`. The owner told the agent to record this already-written work anyway.
- Draft PR into `develop` is the delivery step for this task.

## Open Questions

- None

## Activity Log

- 2026-10-18: Owner asked for the three Execution settings, then asked that they be recorded as a requirement and task, moved to a task branch, and committed.
- 2026-10-18: REQ-0019 approved from that request. Task created and moved to doing on `factory/task-0031-node-execution-settings`.
- 2026-10-18: Implementation was written on `develop` before this task existed. The implementation commit places only that work on the task branch. Other local editor edits stay unstaged.
- 2026-10-18: Moved to review. Draft PR #34 opened into `develop`: https://github.com/quinguyen1502/langgraph-studio/pull/34
- 2026-10-18: Owner asked to finish and merge. REV-0030 has no blocking findings. QA-0030 passed (37 pytest, tsc, diff check). Task set to done.

## Handoff Notes

- Branch `factory/task-0031-node-execution-settings`. PR #34.
- Do not fold unrelated local editor edits into this task.
