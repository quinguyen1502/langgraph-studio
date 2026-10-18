# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0021
- Status: done
- Owner: Grok Bot (agent)
- Created: 2026-10-17
- Updated: 2026-10-17
- Requirement IDs: REQ-0003, REQ-0004, REQ-0005, REQ-0008, REQ-0010 (follow-ups)
- Design IDs: DEC-0018
- Architecture IDs: ARCH-0001

## Objective

Resolve the remaining limits of DEC-0017 and provide UI screenshots for review.

## Scope

- (a) Idempotency keys per run + node + iteration (`Idempotency-Key`), node-result ledger reused on recovery.
- (b) Checkpoints for fan-out/parallel steps (LangGraph superstep checkpoints); imported workflows checkpointed via a serialized in-memory saver.
- (c) Fencing tokens (`runs.lease_gen`) checked on every run write; stale workers stop.
- (d) Export the lost segment's root span (same span id) and link the recovered segment.
- (e) Live notification push (WebSocket, Redis pub/sub / in-memory), polling fallback, HTML e-mail, per-user preferences dialog.
- Screenshots at 1440x900, light/dark, en/vi, with a contact sheet.

## Acceptance

- Migration `0009_effectively_once` on SQLite and Postgres; new code `NOTIFICATION_PREFS_INVALID` in catalog, docs, en + vi.
- Tests on SQLite and Postgres + Redis; Playwright e2e for live push and the settings dialog.

## Links

- DEC-0018, REV-0015, QA-0015; branch `factory/task-0021-effectively-once`.

## Activity Log

- 2026-10-17: Status set to done to match the done/ folder. Previous Status was `review`. Review REV-0015. QA QA-0015.
