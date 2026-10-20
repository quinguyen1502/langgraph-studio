# Requirement

## Metadata

- Project: superstep
- Requirement ID: REQ-0040
- Status: Accepted
- Owner: Thái Quí Nguyễn
- Created: 2026-10-20
- Updated: 2026-10-20
- Source: owner request in chat, 2026-10-20. The owner asked for more templates in the library and for the logos of
  Slack, Telegram and the other platforms, so the channels are easy to recognise. The owner accepted the proposal as
  written: brand colours, 8 templates, requirement and tasks before code.

## Summary

- Add 8 built-in templates. Five show approval through one channel each; three show multi-level approval, support
  escalation and batch processing.
- Show each approval channel's logo, in its brand colours, wherever the UI names a channel.

## Problem Or Opportunity

- The library has 4 built-in templates. Only **Approval flow** shows a Human node, and none shows an approval channel.
  A new user has no example of approving from Slack, Telegram, WhatsApp, e-mail or Teams.
- Channels are named only in text, in several places. A logo makes each platform recognisable at a glance.
- Built-in template names and descriptions are English only, even in the Vietnamese UI.

## Scope

### In Scope

- **Templates.** Eight new built-in templates in `backend/app/engine/templates.py`:

  | ID | Name | Graph |
  | --- | --- | --- |
  | `builtin-approval-slack` | Approve in Slack | Draft (LLM) → Human, channel `slack` → Condition → Polish (LLM) or End |
  | `builtin-approval-telegram` | Approve in Telegram | Same, channel `telegram` |
  | `builtin-approval-whatsapp` | Approve in WhatsApp | Same, channel `whatsapp` |
  | `builtin-approval-email` | Approve by e-mail | Draft → Human, channel `email` → Condition → Send email with the result |
  | `builtin-approval-teams` | Approve in Microsoft Teams | Same as Slack, channel `teams` |
  | `builtin-approval-multilevel` | Two-level approval | Draft → Human (team lead, Slack) → Condition → Human (manager, e-mail) → Condition → End |
  | `builtin-support-escalation` | Support with escalation | Retriever → LLM answer → Decision (confident?) → End, or Human review → End |
  | `builtin-batch` | Batch processing | For each over a list → LLM summary per item → joined result → End |

  - The final labels, prompts and positions are set in the task. The table fixes the intent and the node types.
- **Channels in templates.** A template stores only the channel **kind** (`data.approval.channel`). It stores no
  connection (`channel_id`), target or approvers, so the user picks their own after creating the workflow.
- **Template names in both languages.** Every built-in template, the 4 existing ones included, shows its name and
  description in the UI language (en, vi). Saved and imported templates keep the name their author wrote.
- **Channel logos.** One shared component renders the logo of a channel kind. It is used in:
  - Settings → Channels: each platform card title;
  - Settings → My accounts: each linked account;
  - the Human node's approval channel select;
  - the Audit log: platform filter and rows;
  - template gallery cards: the logos of the channels the template uses.
- **Decision.** A new decision record that allows official brand colours for these logos as the one exception to
  DEC-0008 rule 3 (no hard-coded colours). `docs/ui-conventions.md` and its colour check are updated to match.
- **Docs.** The handbook (en, vi) lists the new templates and shows the logos in the updated screenshots.

### Out Of Scope

- New approval channels, or changes to how channels send or receive.
- Logos for model providers, MCP servers or other integrations.
- A template marketplace, or template categories and search.
- Translating names of templates that users save or import.

## Stakeholders Or Users

- Workflow authors who pick a starting point in **New workflow**.
- Admins and users who connect channels and link their accounts.

## Current Context

- Built-in templates: `backend/app/engine/templates.py` (`BUILTINS`, `BUILTIN_IDS`), REQ-0015 / TASK-0025.
  `tests/test_templates.py` checks that built-ins are well formed and pins the first four IDs.
- Gallery: `frontend/src/components/template-gallery.tsx` and `template-preview.tsx`. They show `tp.name` and
  `tp.description` from the API.
- Approval channels: REQ-0003, REQ-0034, DEC-0019, DEC-0037. Kinds are `slack`, `telegram`, `whatsapp`, `email` and
  `teams`, labelled by `approvals.kind.*` in the locales.
- A Human node's `data.approval` holds `channel_id`, `channel` (the kind), `target` and `approvers`.
  `ApprovalService.on_waiting` sends nothing when the channel needs a target and none is set. With only a kind,
  `ChannelService.for_node` uses the owner's connection of that kind; with none, the Audit log gets a
  `CHANNEL_NOT_FOUND` entry. Either way the run waits and can be answered in the studio.
- UI rules: DEC-0008 and `docs/ui-conventions.md`, rule 3: no hard-coded colours.
- Logo sources: Simple Icons (CC0 paths) has Telegram and WhatsApp. It no longer has Slack or Microsoft Teams, which
  were removed at the brand owners' request. E-mail is sent over generic SMTP and has no brand.

## Desired Behavior

- **New workflow** shows 12 built-in templates: the 4 existing ones first, then the 8 new ones.
- A card for a template with an approval channel shows that channel's logo, or the logos of all its channels.
- Creating a workflow from a channel template opens a graph where the Human node already names the channel kind.
  Running it without a connection waits at the Human node and can be approved in the studio.
- After connecting a channel and setting a target, the same workflow sends the request to that channel.
- Settings → Channels, My accounts, the Human node select and the Audit log show the logo next to each channel name.
- With the UI in Vietnamese, built-in template names and descriptions are in Vietnamese.

## Business Rules

- Logos are the platforms' own marks, in their official colours, unmodified. They identify an integration and do not
  suggest endorsement.
  - Slack: the Slack Media Kit.
  - Microsoft Teams: Microsoft's official product icon.
  - Telegram and WhatsApp: Simple Icons, in the brand colour it records.
- E-mail uses a generic mail icon in theme colours, not a provider's logo.
- Every logo has a text label next to it or an accessible name, so it is never the only cue.

## Constraints

- shadcn components and theme tokens. The only hard-coded colours allowed are in the single logo file, as set by the
  new decision.
- en and vi locale keys stay identical. No UI text is written in components.
- Templates run in mock mode with no API key and no connected channel.
- No API or schema change is expected. Channel kinds per template are read from the template graph.
- Downloading the Slack and Teams logo files needs the owner's permission at implementation time.

## Acceptance Criteria

- The 8 templates are listed, are well formed, pass the validator, and run in mock mode up to their first Human node
  (or to the end, for the batch template).
- Each channel template stores the channel kind and no `channel_id`, `target` or `approvers`.
- Built-in template names and descriptions show in en and vi, for all 12.
- The logo appears in the 5 places listed in scope, for all 5 channel kinds, in light and dark themes.
- The decision record exists, and `docs/ui-conventions.md` and its colour check allow brand colours only in the logo
  file.
- Backend tests cover the new templates. Unit or e2e tests cover the logo component and the gallery card logos.
- The handbook's template and channel pages (en, vi) are updated, and both builds pass.

## Edge Cases

- A template with two channels (two-level approval) shows both logos once each.
- A saved or imported template with a Human node on a channel shows the logo too, since it is read from the graph.
- An unknown channel kind, for example from an older file, shows a generic icon and its raw name.
- Teams needs no target, so a run of the Teams template with no Teams connection adds a `not_configured` entry
  (`CHANNEL_NOT_FOUND`) to the Audit log. This is existing behaviour and is expected.
- Dark theme: the logos stay readable. Where a brand mark needs it, the logo sits on a light tile.

## Assumptions

- The owner's choice of brand colours over monochrome logos stands for all five places.
- The **Decision** and **For each** nodes (REQ-0035, REQ-0036) are stable enough to use in built-in templates.

## Open Questions

- None. The owner accepted the proposal on 2026-10-20.

## Related Artifacts

- REQ-0015 template library (`.factory-state/artifacts/REQ-0015-template-library.md`), TASK-0025
- REQ-0003 human in the loop, REQ-0034 more approval channels, DEC-0019, DEC-0037
- REQ-0035 For each node, REQ-0036 Decision node, REQ-0037 Send email node
- DEC-0008 UI conventions (`docs/ui-conventions.md`)
- Handbook: `handbook/docs/*/guide/templates.md`, `handbook/docs/*/operate/channels.md`
