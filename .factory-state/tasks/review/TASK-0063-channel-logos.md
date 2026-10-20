# Task

## Metadata

- Project: superstep
- Task ID: TASK-0063
- Status: review (REV-0057, QA-0057)
- Owner: Thái Quí Nguyễn
- Created: 2026-10-20
- Updated: 2026-10-20
- Requirement IDs: REQ-0040
- Design IDs: none (UX direction set in REQ-0040)
- Architecture IDs: DEC-0008, DEC-0042 (to write in this task)

## Objective

Show each approval channel's logo, in its brand colours, wherever the UI names a channel. Record the brand-colour
exception to DEC-0008 rule 3 as DEC-0042.

## Scope

### In Scope

- **DEC-0042 Brand logos.** Official brand colours are allowed only in the channel logo file. Marks are used
  unmodified, next to a text label or with an accessible name.
- **`docs/ui-conventions.md`.** Rule 3 points to DEC-0042, and the checklist's colour command excludes the logo file.
- **Logo component.** `frontend/src/components/approvals/channel-logo.tsx` exports `ChannelLogo` with props `kind` and
  `className`, using inline SVG.
  - Slack and Microsoft Teams: SVG from the official brand kits (Slack Media Kit; Microsoft's Teams product icon).
  - Telegram and WhatsApp: Simple Icons paths (CC0), in the brand colour Simple Icons records.
  - E-mail: lucide `Mail` in theme colours.
  - Unknown kind: lucide `MessageSquare` in theme colours.
  - Sized like a lucide icon (`size-4` by default). `aria-hidden` when a text label is next to it; otherwise
    `role="img"` with the kind's label.
- **Use it in:**
  - `pages/settings/ChannelsSection.tsx`: platform card title;
  - Settings → My accounts: each linked account row (`components/approvals/identity-row.tsx`);
  - `components/human-approval-settings.tsx`: the channel select items and trigger;
  - `pages/settings/AuditSection.tsx`: platform filter options and the platform shown on each row;
  - `components/approvals/channel-parts.tsx`: the connection item heading.
- **Docs.** `handbook/docs/*/operate/channels.md` mentions the logos; retake `settings-channels.png` (en, vi) and
  other screenshots where a channel name now has a logo.

### Out Of Scope

- Template gallery cards: TASK-0064 uses `ChannelLogo` there.
- Logos for model providers or MCP servers.
- Any change to channel behaviour or the API.

## Inputs

- REQ-0040, DEC-0008, `docs/ui-conventions.md`.
- Channel kinds: `frontend/src/lib/approvals.ts` (`ChannelKind`), locale keys `approvals.kind.*`.

## Related Artifacts

- Requirements: `.factory-state/artifacts/REQ-0040-channel-templates-and-logos.md`
- Design: none
- Architecture: `docs/ui-conventions.md` (DEC-0008)
- Decisions: DEC-0008, DEC-0019, DEC-0037; DEC-0042 (new)
- Discovery: Simple Icons 16.35.0 has `telegram` and `whatsapp` but no `slack` or `microsoftteams` (removed at the
  brand owners' request).
- Clarifications: none

## Expected Outputs

- `.factory-state/decisions/DEC-0042-brand-logos.md`
- `frontend/src/components/approvals/channel-logo.tsx` and its unit test
- The five call sites above, updated
- `docs/ui-conventions.md` updated
- Handbook text and screenshots updated (en, vi)

## Implementation Notes

- Put the SVG sources' origin and licence in a comment at the top of `channel-logo.tsx`.
- Slack's mark is multi-colour; Teams' icon has its own tile. Both stay readable on dark backgrounds. Check Telegram
  and WhatsApp in dark mode; if contrast is poor, put them on a small `bg-background` tile, not a new colour.
- Keep the label text: the logo goes next to the name and does not replace it.

## Constraints

- shadcn and theme tokens everywhere else. No new hard-coded colour outside `channel-logo.tsx`.
- en/vi keys identical. No new UI text expected, other than an accessible-name fallback if one is needed.
- Downloading the Slack and Teams files needs the owner's permission at implementation time. Name the file, its source
  and its size when asking.

## Dependencies

- None. TASK-0064 depends on this task for the gallery logos.

## Acceptance Criteria

- `ChannelLogo` renders the right mark for `slack`, `telegram`, `whatsapp`, `email` and `teams`, and a generic icon
  for an unknown kind.
- The logo appears in all five call sites, in light and dark themes.
- DEC-0042 exists. `docs/ui-conventions.md` rule 3 and the checklist allow brand colours only in `channel-logo.tsx`,
  and the colour check finds nothing elsewhere.
- Every logo has a visible label next to it or an accessible name.
- `npm run build`, lint, vitest and the e2e suite pass. The handbook builds in en and vi.

## Validation Plan

- Vitest: `ChannelLogo` for each kind and the unknown fallback (accessible name, no throw).
- E2E: Channels page shows a logo per platform card; the Human node select shows logos.
- Manual: light and dark screenshots of the five places.
- `docs/ui-conventions.md` checklist commands.

## Assumptions

- Brand colours were chosen by the owner on 2026-10-20 (REQ-0040).

## Open Questions

- None.

## Activity Log

- 2026-10-20: planned from REQ-0040.
- 2026-10-20: started and implemented. The owner allowed downloading the four logo files: Slack and Teams from
  Wikimedia Commons, Telegram and WhatsApp from Simple Icons 16.35.0. Review REV-0057, QA QA-0057.

## Handoff Notes

- Next: owner review of the PR, then merge. TASK-0064 starts after the merge.
