# Decision Record

## Metadata

- Project: superstep
- Decision ID: DEC-0042
- Status: Accepted
- Owner: Thái Quí Nguyễn
- Created: 2026-10-20
- Updated: 2026-10-20
- Related Requirements: REQ-0040
- Related Architecture: DEC-0008 (UI conventions, `docs/ui-conventions.md`)
- Related Tasks: TASK-0063, TASK-0064

## Context

REQ-0040 shows each approval channel's logo wherever the UI names a channel. The owner chose official brand colours
over monochrome marks so the platforms are recognisable at a glance. DEC-0008 rule 3 forbids hard-coded colours in
components.

## Decision

1. **One exception to DEC-0008 rule 3.** Official brand colours are allowed in exactly one file,
   `frontend/src/components/approvals/channel-logo.tsx`. Every other component keeps theme tokens only.
2. **`ChannelLogo({ kind, className })`** is the only way to show a channel's logo.
   - Slack, Telegram, WhatsApp and Microsoft Teams render their own marks as inline SVG, unmodified and in their
     official colours.
   - E-mail has no brand (generic SMTP), so it uses lucide `Mail` in theme colours.
   - An unknown kind uses lucide `MessageSquare` in theme colours.
3. **Marks identify an integration.** They are never stretched, recoloured or combined with other marks, and they do not
   suggest endorsement. The file records each mark's source and licence in a comment.
4. **Accessibility.** A logo next to a visible label is `aria-hidden`. A logo shown alone gets `role="img"` and the
   kind's label (`approvals.kind.*`) as its name.
5. **Sizing.** Logos default to `size-4`, like lucide icons, and follow `className`. They sit inline with the label.
6. **Checklist.** `docs/ui-conventions.md` rule 3 names this exception. The review checklist adds a hex-colour check
   that excludes only this file.

## Rationale

- Brand colours are what make a platform recognisable. Monochrome marks were the alternative, and the owner chose
  colour.
- One file keeps the exception reviewable, and the checks catch any colour that leaks elsewhere.

## Alternatives Considered

- **Monochrome marks in `currentColor`.** These need no exception, but are less recognisable. Not chosen by the owner.
- **A brand-colour CSS variable per platform in `index.css`.** This spreads brand values into the theme, and Slack's
  mark has four colours. Rejected.
- **An icon package.** Simple Icons no longer ships Slack or Microsoft Teams, and its marks are single-colour. Rejected
  for those two marks; its Telegram and WhatsApp paths (CC0) are used.

## Consequences

- New brand marks, if any are ever needed, go in the same file under the same rules.
- Brand owners can change their marks. Updating them is a manual edit of this file.
