# Decision

## Metadata

- Project: langgraph-studio
- Decision ID: DEC-0017
- Task ID: TASK-0020
- Status: proposed (draft PR)
- Created: 2026-10-17
- Supersedes: the "Deferred" list of DEC-0016

## Decisions

### 1. Notifications for waiting runs
- `notifications` table (user, run, kind `run_waiting`/`run_expired`, title, body, link, read_at). `RunService.record` calls `NotificationService.run_event` on waiting/expired.
- In-app: `GET /api/notifications[?unread=1]`, `POST /api/notifications/{id}/read`, `POST /api/notifications/read-all`. Header bell (shadcn DropdownMenu), polled every 30 s.
- E-mail via `smtplib` when `SMTP_HOST` is set (STARTTLS/SSL/auth optional); unset = no-op. Generic notify webhook `STUDIO_NOTIFY_WEBHOOK_URL`, signed with `STUDIO_NOTIFY_WEBHOOK_SECRET` (same `X-Studio-Signature` scheme). Both run off the request path in a background thread; failures are logged and never fail the run.

### 2. Webhook deliveries
- `webhook_deliveries` table: run, workflow, token, url, event, payload, status (`pending|succeeded|failed`), attempts, last response code, latency_ms, error, next_attempt_at.
- Each result callback creates a delivery and enqueues a `delivery` job. `DeliveryService.attempt` posts (DNS-pinned, signed); retryable failures (network errors and any non-2xx response; an address refused by the SSRF guard is not retryable) are re-enqueued with `min(BASE**n, MAX)` seconds delay via the queue's delayed set; non-retryable or `STUDIO_WEBHOOK_MAX_ATTEMPTS` reached = `failed`.
- `GET /api/workflows/{wid}/deliveries`, `POST /api/workflows/{wid}/deliveries/{id}/redeliver` (resets attempts). UI: "Deliveries" tab in the API dialog.
- Secret rotation `POST /api/workflows/{wid}/tokens/{tid}/rotate-secret`: the new secret is shown once; the previous one is kept in `signing_secret_prev` for `STUDIO_SECRET_GRACE` seconds and callbacks carry both `v1=` values, so receivers can switch without downtime.

### 3. Recovery from checkpoints
- The engine yields an internal checkpoint after every node when exactly one non-end node is next; `RunService` persists it as run progress (reusing the HITL checkpointer/resume path). A `recovered` job resumes from the last checkpoint (`run_recovered` event); without a checkpoint it restarts from scratch. The recovery gap is excluded from `duration_ms`.

### 4. Stale-job reaper
- Heartbeats are replaced by per-job leases: `studio:job-lease:<sha1(job)>` with TTL `STUDIO_JOB_VISIBILITY_TIMEOUT`, renewed every timeout/3 while the job runs, deleted on ack. A maintenance loop every `STUDIO_JOB_REAP_EVERY` seconds promotes due delayed jobs and requeues processing-list jobs whose lease has been missing on two consecutive sweeps (as `recovered`).

### 5. Telemetry
- Spans are exported live: a run root span starts with the run and each node span is exported as the node finishes; resumed/recovered segments are new root spans linked to the previous one (trace context stored in the checkpoint). Unconfigured = no-op, unchanged.
- `STUDIO_OTEL_METRICS=1` + OTLP endpoint: counters/histograms `studio.runs`, `studio.run.duration`, `studio.tokens`, `studio.cost`, `studio.errors` with `status`, `source` attributes.

## Idempotency limits (side-effect nodes)
- Execution stays **at-least-once**. After a crash, the node that was in flight (and only that node, when a checkpoint exists) runs again. HTTP/tool/code nodes with side effects must be idempotent (e.g. send an idempotency key derived from `run_id` + node id).
- Fan-out steps (several next nodes) and imported (code) workflows produce no checkpoint and restart from the beginning.
- A worker that lost its lease (e.g. a long GC pause) may still finish while another worker re-runs the job; the run record is an upsert, so the last writer wins.
- Webhook deliveries are at-least-once; receivers should de-duplicate on `run_id` + event.

## Not done
- Exactly-once execution (needs transactional outbox + idempotent tools; out of scope).
- The root span of a crashed segment is never exported (its node spans are).
- Plain-text e-mail, no per-user notification preferences, no push/websocket for the bell (polling).
