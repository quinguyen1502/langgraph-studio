# Decision Record

## Metadata

- Project: langgraph-studio
- Decision ID: DEC-0037
- Status: Accepted
- Owner: Thái Quí Nguyễn
- Created: 2026-10-19
- Updated: 2026-10-19
- Related Requirements: REQ-0034, REQ-0003
- Related Architecture:
- Related Tasks: TASK-0047

## Context

DEC-0019 built the approval adapter interface and implemented Slack and Telegram; WhatsApp, Teams, and e-mail were left for later. The owner asked for them (remaining-work item 7). The three platforms differ:

- WhatsApp's Cloud API has reply buttons and signed webhooks. It delivers free-form messages only within 24 hours of the person's last message.
- A Teams bot that receives button presses needs an Azure Bot registration and a Bot Framework JWT check.
- E-mail has no buttons that can post back.

## Decision

1. **WhatsApp** is a button channel, like Slack and Telegram.
   - Reply buttons carry the signed tokens.
   - The webhook is checked with `X-Hub-Signature-256` (the app secret). `GET` on the callback URL answers Meta's `hub.challenge` with the owner's verify token.
   - An optional approved template with two quick-reply buttons sends the request outside the 24-hour window.
   - Approvers verify their WhatsApp number with a code.
   - WhatsApp cannot edit a message, so the outcome is a reply to the request.
2. **E-mail and Teams are link channels** (`link_based`).
   - The message links to `/approve?token=…`. The person signs in to the studio and confirms with a POST.
   - The studio account is the identity, so there is no chat account to link, and opening a link decides nothing.
   - Owner and approver rules, single use, expiry, and audit are the same as for button channels (`ApprovalService._decide`).
   - E-mail goes through the studio's SMTP settings to the comma-separated addresses in the node's target.
   - Teams posts an Adaptive Card to a Workflows webhook. It needs no target, and each webhook is its own connection. The outcome is posted as a second card.
   - The webhook URL gets the outbound address guard and IP pinning, and must be HTTPS unless `STUDIO_ALLOW_PRIVATE_CALLBACKS=1`.

## Rationale

- Signing in on the studio page gives a strong identity without per-platform account linking.
- A Workflows webhook needs no Azure resources. The trade-off is that the card cannot change in place.

## Alternatives Considered

- Option: A Teams bot through the Bot Framework
  - Benefits: Buttons that answer inside Teams, and cards that update in place
  - Tradeoffs: An Azure Bot registration per deployment, a JWT check against Microsoft's keys, and stored conversation references for proactive messages
  - Reason Not Chosen: Much more setup for the same decision
- Option: E-mail links that decide on GET
  - Benefits: One click
  - Tradeoffs: Mail scanners and link previews open links and would approve requests
  - Reason Not Chosen: Unsafe

## Impacts

- `ApprovalChannel` has `link_based`, `target_required`, and `challenge()`. Identity slots skip link channels. The kinds payload carries both flags for the UI.
- New page `/approve` and API `GET|POST /api/approvals/link`.
- The e2e environment sets `STUDIO_PUBLIC_URL` to the UI, and the mock chat server answers `/teams/…`.

## Risks

- WhatsApp verification codes, and button messages without a template, need the 24-hour window. The UI and the README say so.

## Follow-Up

- None
