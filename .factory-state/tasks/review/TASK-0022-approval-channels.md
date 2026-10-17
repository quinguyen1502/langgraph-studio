# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0022
- Status: review
- Owner: Grok Bot (agent)
- Created: 2026-10-17
- Updated: 2026-10-17
- Requirement IDs: REQ-0003 (follow-up)
- Design IDs: DEC-0019
- Architecture IDs: ARCH-0001

## Objective

Approve or reject waiting runs from external channels, starting with Slack and Telegram, behind an adapter interface that also fits WhatsApp, Teams and e-mail later.

## Scope

- `ApprovalChannel` adapters (send_request, verify + handle_callback, acknowledge, update) for Slack and Telegram, plus a registry.
- Signed, single-use, expiring approval tokens.
- Channel identities per user; only the run owner or the listed approvers may decide.
- Audit log of every request, decision and refused attempt.
- The original message is edited after the decision. Answering in the studio, cancel and expiry close open requests.
- Per-Human-node channel config (channel, target, approvers) in the node settings UI.
- "Approval channels" dialog: connections, my accounts, audit log.
- Channel secrets are Fernet-encrypted (core/crypto). Without a configured channel nothing happens (no-op).

## Acceptance

- Migration `0010_approval_channels` runs on SQLite and Postgres.
- New error codes are in the catalog, docs, en and vi.
- pytest on SQLite and on Postgres + Redis, with mocked Slack/Telegram APIs and signed callbacks.
- Playwright e2e for the UI.
- README setup guides, DEC-0019, REV-0016, QA-0016.
- Screenshots in 4 variants.

## Links

- DEC-0019, REV-0016, QA-0016; branch `factory/task-0022-approval-channels`.
