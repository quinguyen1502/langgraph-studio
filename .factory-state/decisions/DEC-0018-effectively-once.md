# Decision

## Metadata

- Project: langgraph-studio
- Decision ID: DEC-0018
- Task ID: TASK-0021
- Status: proposed (draft PR)
- Created: 2026-10-17
- Supersedes: the "Not done" list and part of "Idempotency limits" of DEC-0017

## Decisions

### (a) Effectively-once side effects
- `engine/effects.py`: every LLM/Tool node execution has a stable key `studio-<sha256(run_id:node_id:iteration)[:32]>`.
  HTTP Tool nodes send `Idempotency-Key`, `X-Studio-Run-Id`, `X-Studio-Attempt`; Python tools receive it when they declare
  an `idempotency_key` parameter. A recovered job re-executing the same node sends the **same** key (the iteration comes
  from the checkpointed counters), so idempotent receivers apply it once. The attempt number is separate.
- Node-result ledger `node_results (run_id, node_id, iteration) -> delta, idempotency_key` (migration 0009). Before a
  side-effect node runs, a recorded result is returned instead (`node_finished.reused = true`); after it runs, its update
  is recorded (first writer wins). Used for every run (also UI runs, e.g. a sibling branch of a paused Human node) and
  purged when the run reaches a final status.

### (b) Checkpoints from LangGraph itself
- The runtime compiles the graph with an in-memory LangGraph saver and observes `stream_mode="checkpoints"`, i.e. real
  superstep boundaries with their `next` tasks. A step with several parallel nodes is checkpointed as
  `{nodes: [...], state, counts}` and resumed by starting the graph at all of them (multiple START edges).
- A Human node in a parallel branch pauses with its siblings in the checkpoint; they resume together and the siblings'
  results come from the ledger.
- Imported graphs (subprocess): the sandbox runner attaches an in-memory saver **when the graph has no checkpointer of its
  own**, streams each superstep checkpoint serialized with LangGraph's own serde (msgpack, base64, ≤ 2 MB) with
  `durability="sync"`, and a fresh subprocess restores it (`saver.put`) and continues with `astream(None)`.

### (c) Fencing tokens
- `runs.lease_gen`: a worker claims a run by compare-and-set (`queued` → `running`, or `running` for a recovered job) and
  gets generation N+1. Every write of that job carries N+1: progress checkpoints, ledger rows, the final record. A write
  with an older generation raises `StaleLease` and nothing is written.
- A fenced-out worker stops at once (a guard is also checked before each side-effect node), closes its trace segment as
  cancelled, does not touch the run bus entry, records nothing, and does not create the result webhook delivery.
- Each requeue increments the job's `attempt`, so every attempt has its own Redis lease key; a stale worker's
  `touch`/`ack` cannot extend or delete the new owner's lease.

### (d) Lost trace segments
- Checkpoints store the segment ref `{trace_id, span_id, name, started, parent}`, saved once right at the start of every
  queue segment. On recovery, `Telemetry.close_lost` exports the lost root with **the same span id** (custom id
  generator), so the node spans it already exported get their parent; status ERROR "worker lost". The recovered segment is
  its child and also carries a span link to it.

### (e) Notifications
- Live push: `NotificationHub` (Redis pub/sub `studio:notify:<user>`, in-memory fallback), WebSocket
  `/ws/notifications?token=`. The bell connects, shows `data-live`, and polls every 30 s only while the socket is down.
- E-mail is multipart: plain text + an inline-styled HTML template (all values escaped).
- Preferences `users.notify_in_app` / `users.notify_email`; `GET/PUT /api/notifications/preferences`
  (`NOTIFICATION_PREFS_INVALID`, 422). In-app off: no row, no push. E-mail off: no e-mail. The notify webhook is
  server-wide and not affected.

## Remaining limits
- Effectively-once needs cooperating receivers: a side effect that ignores `Idempotency-Key` can still be applied twice
  when a worker dies **during** that node (before its result is recorded). LLM provider calls have no idempotency key: a
  crash mid-call repeats that call (and its cost) once.
- Fencing is checked before a side effect starts, not during it: a worker that loses its lease in the middle of a node
  finishes that node's side effect, but its result is rejected; the new owner repeats it with the same key.
- Imported graphs: no ledger and no idempotency keys inside user code (the nodes run in the user's process); graphs that
  bring their own checkpointer are not checkpointed by us; state that LangGraph's serde cannot serialize, or a checkpoint
  over 2 MB, means a restart from the beginning.
- Push is fire-and-forget (pub/sub); a missed push is caught by the next poll or when the dropdown opens.
- The HTML e-mail is English only (no per-user language yet); preferences are per channel, not per workflow.
