# Task

## Metadata

- Project: superstep
- Task ID: TASK-0076
- Status: todo
- Owner: Thái Quí Nguyễn
- Created: 2026-10-22
- Updated: 2026-10-22
- Requirement IDs: REQ-0044
- Design IDs: none (UX set in REQ-0044)
- Architecture IDs: DEC-0008, DEC-0046

## Objective

Let owners manage chat triggers in the editor, show the Slack events URL and missing scopes on the Channels page, and
mark chat runs in the run history.

## Scope

### In Scope

- **Chat triggers dialog** (`components/chat-triggers-dialog.tsx`):
  - it opens from **Chat triggers** in the ⋯ menu and the command palette (`action:chat-triggers`, owners only, like
    schedules) and is disabled for imported repositories;
  - the list shows each trigger's name, platform logo with connection and place, command, on/off switch, last
    message, last run link and stop note;
  - the add and edit form has:
    - name;
    - connection: the user's Slack and Telegram connections, with a "not connected" hint linking to Channels;
    - where: direct messages or a channel/group id, with a hint on where to find it;
    - command;
    - input field and reply field: selects from the saved graph;
  - delete asks for the typed name (`ConfirmDeleteDialog`);
  - API errors show through `errorText`;
  - a sample line ("In #hr: @Superstep leave <text>") previews the command.
- **Channels page:**
  - a Slack connection shows the events URL (copy button) and a warning listing missing chat-trigger scopes, with
    "Reinstall" (Add to Slack);
  - a Telegram connection hints that "Register webhook" must be pressed again to receive messages.
- **Run history:**
  - a "Chat" source badge with the platform;
  - the run detail shows the sender's chat account and the trigger name.
- **Locales:**
  - `chatTriggers.*`, and the new `channels.*` / `history.*` keys, in en and vi with identical keys;
  - no literal UI text.
- **e2e** `frontend/e2e/chat-triggers.spec.ts`:
  - add a trigger, refuse a duplicate command (error shown), switch it off and on, and delete it by typed name;
  - the history badge on a run with `source="chat"`;
  - the Slack scope warning, from a mocked connection response.
- vitest for any pure helpers, such as the sample line.

### Out Of Scope

- Backend behaviour (TASK-0074, TASK-0075) and the handbook page (TASK-0077).

## Inputs

- TASK-0074 API, TASK-0075 run fields.
- `frontend/src/components/schedules-dialog.tsx`, `api-trigger-dialog.tsx`, `components/editor/use-studio.ts`,
  `editor-run-panel.tsx` (history badge), the Channels page components, `ConfirmDeleteDialog`, `docs/ui-conventions.md`.

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0044-chat-triggers.md`
- Clarification: `.factory-state/artifacts/CLAR-0002-chat-triggers.md`
- Design: none
- Architecture: `docs/ui-conventions.md` (DEC-0008)
- Decisions: DEC-0046
- Discovery: none

## Expected Outputs

- Dialog, menu and palette command, Channels page additions, history badge and sender, locales, e2e

## Implementation Notes

- Follow the schedules dialog's layout and its share-right gating.
- Platform logos already exist from REQ-0040.

## Constraints

- shadcn components and theme tokens only. en and vi keys identical. `api()` only. Delete by typed name. Works at
  900 px and in both themes (the DEC-0008 checklist).

## Dependencies

- TASK-0074, TASK-0075.

## Acceptance Criteria

- An owner adds, edits, switches and deletes (typed name) chat triggers from the editor. Errors show translated.
- The Channels page shows the Slack events URL and any missing scopes. Telegram shows the re-register hint.
- Chat runs show a Chat badge, the platform and the sender in the history.
- tsc, lint, vitest, build and Playwright pass.

## Validation Plan

- `npx tsc -b`, `npm run lint`, `npx vitest run`, `npm run build`, `npx playwright test`.
- A visual check in light and dark themes at 900 px.

## Assumptions

- None beyond REQ-0044.

## Open Questions

- None.

## Activity Log

- 2026-10-22: planned from REQ-0044.

## Handoff Notes

- None.
