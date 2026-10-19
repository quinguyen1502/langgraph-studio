# Human approval

A **Human** node pauses the run in status `waiting` and asks its `prompt`.
The answer goes to the node's `output_field`, so a Condition after it can
branch on it.

![A run waiting for approval](../images/human-waiting.png)

## Answer in the studio

The Logs tab shows the question with **Approve** (`approved`), **Reject**
(`rejected`), or a free-text **Send response**. Only the run's owner can answer
or cancel here; approvers listed on the node answer through an
[approval channel](#approve-from-chat).

Runs waiting for you are listed at the top of **Workflows** under **Waiting
for you**, and the header badge counts them. **Respond** opens the run.

![Workflows with a waiting run](../images/workflows.png)

Checkpoints live in the database, so a restart resumes the run where it
stopped. Waiting time does not count toward the run's duration. A wait longer
than `STUDIO_WAIT_TTL` seconds (default 7 days; `0` never expires) becomes
`expired`, and resuming then returns `410 RUN_EXPIRED`.

```text
GET  /api/runs/pending
WS   /ws/run   {"resume_run_id": "…", "response": "approved"}
POST /api/runs/{id}/cancel
```

## Notifications

The bell lists unread notifications and receives them live on
`/ws/notifications`, with a 30 s poll as fallback. Each user picks what they
receive under **Settings → Profile**.

| Channel | Set up |
| --- | --- |
| In-app bell | Always on |
| E-mail | `SMTP_HOST` (and `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_STARTTLS` or `SMTP_SSL`); links use `STUDIO_PUBLIC_URL` |
| Webhook | `STUDIO_NOTIFY_WEBHOOK_URL` posts JSON for each `waiting` or `expired` run, signed with `STUDIO_NOTIFY_WEBHOOK_SECRET` when set |

## Approve from chat

A Human node can also send the request to an **approval channel**:

| Channel | Carries | The answer |
| --- | --- | --- |
| Slack | Approve / Reject buttons | a button press by a verified Slack account |
| Telegram | Approve / Reject buttons | a button press by a verified Telegram account |
| WhatsApp | Two reply buttons | a reply by a verified phone number |
| E-mail | Approve / Reject links to `/approve?token=…` | confirmed in the studio after sign-in |
| Microsoft Teams | An Adaptive Card with links | confirmed in the studio after sign-in |

The same rules apply everywhere: only the run owner or an approver listed on
the node, one answer, and an expiry (`STUDIO_APPROVAL_TTL`, default 86400 s).
Button tokens are HMAC-signed and single-use. Messages follow the run owner's
language. Answering in the studio disables the chat buttons; cancel and expiry
close the request. With no channel configured, nothing is sent.

Setting up each channel is in [Approval channels](../operate/channels.md).

## A typical pattern

```text
Start → LLM (draft a reply) → Human (approve the draft?) → Condition on decision
      ├─ approved → Send email → End
      └─ rejected → End
```

The **Approval flow** starter template has this shape.
