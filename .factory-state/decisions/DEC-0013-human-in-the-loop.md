# Decision Record

## Metadata

- Project: langgraph-studio
- Decision ID: DEC-0013
- Status: Accepted
- Owner: Thái Quí Nguyễn
- Created: 2026-10-16
- Updated: 2026-10-16
- Related Requirements: REQ-0003
- Related Architecture: ARCH-0001
- Related Tasks: TASK-0006

## Context

REQ-0003: workflows pause at an approval/input node and resume after a human responds. Resume must survive a server restart. Open question: "Who may approve: owner only or any authenticated user?"

## Decision

1. **Owner only.** Only the user who owns the run (the workflow owner who started it) can see it as pending, resume it or cancel it. Others get `RUN_NOT_FOUND`, the same rule as everything else. Sharing and approval by other users waits for RBAC (TASK-0014).
2. **New node type `human`** (`label`, `prompt` template, `output_field`). With no response yet, the run stops with status `waiting`. The WS event is `run_waiting` {node, label, prompt, state}. The human's response (text) is written to `output_field`. The UI buttons send `approved` / `rejected` (a JSON `true` / `false` maps to the same), so a Condition can branch on them.
3. **Checkpoint stored by the app, not a LangGraph checkpointer (KISS).**
   - Saved in `runs.checkpoint` (JSON {node, state, workflow snapshot}, migration `0004_hitl`).
   - Resuming compiles the same workflow snapshot with the paused node as entry point and continues with the saved state.
   - This works the same on SQLite and Postgres, survives restarts, and needs no extra checkpointer packages or tables. LangGraph's `interrupt()` needs a checkpointer per backend (`langgraph-checkpoint-sqlite` / `-postgres`), which would add a second persistence layer next to Alembic.
4. **One run, one log.** Resume uses the same run id. The WS sends `run_resumed` {node, response}, and events append to the stored events. Metrics and the single OTel trace are produced when the run finally ends; duration is wall time, including the wait.
5. **API**:
   - Resume over the WebSocket: `{resume_run_id, response}`.
   - `GET /api/runs/pending` lists the user's waiting runs.
   - `POST /api/runs/{id}/cancel` also closes a waiting run.
   - New error codes: `RUN_NOT_WAITING` (409), `RUN_RESPONSE_INVALID` (400).

## Consequences

- Imported-repo (`code`) graphs cannot pause; only Studio-built workflows support the Human node.
- No notifications (out of scope); pending runs are visible on the workflow list.
