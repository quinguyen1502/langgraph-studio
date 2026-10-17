# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0020
- Status: done
- Owner: Grok Bot (agent)
- Created: 2026-10-17
- Updated: 2026-10-17
- Requirement IDs: REQ-0003, REQ-0004, REQ-0005, REQ-0008, REQ-0010 (follow-ups)
- Design IDs: DEC-0017
- Architecture IDs: ARCH-0001


## Objective

Resolve the items deferred in DEC-0016.

## Scope

1. Notifications for waiting runs (in-app bell, SMTP e-mail, notify webhook).
2. Webhook delivery log, queued exponential-backoff retry, redelivery UI, signing-secret rotation with grace.
3. Recovered jobs resume from the last LangGraph checkpoint; idempotency limits documented.
4. Periodic stale-job reaper (lease / visibility timeout).
5. Live per-node spans; optional OTLP metrics.

## Acceptance

- Migration `0008_notifications_deliveries` on SQLite and Postgres.
- New error codes `NOTIFICATION_NOT_FOUND`, `DELIVERY_NOT_FOUND` in catalog, docs/api-errors.md, en + vi.
- Tests on SQLite and Postgres + Redis; Playwright e2e for the bell, deliveries and rotation.

## Links

- DEC-0017, REV-0014, QA-0014; branch `factory/task-0020-deferred-hardening`.

## Activity Log

- 2026-10-17: Status set to done to match the done/ folder. Previous Status was `review`. Review REV-0014. QA QA-0014.
