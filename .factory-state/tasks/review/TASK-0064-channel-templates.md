# Task

## Metadata

- Project: superstep
- Task ID: TASK-0064
- Status: review (REV-0058, QA-0058)
- Owner: Thái Quí Nguyễn
- Created: 2026-10-20
- Updated: 2026-10-21
- Requirement IDs: REQ-0040
- Design IDs: none (UX direction set in REQ-0040)
- Architecture IDs: DEC-0009

## Objective

Add 8 built-in templates (five channel approvals, two-level approval, support escalation, batch processing). Show
built-in template names in en and vi, and show channel logos on gallery cards.

## Scope

### In Scope

- **Backend, `backend/app/engine/templates.py`.** Eight new entries in `BUILTINS`, after the four existing ones:
  - `builtin-approval-slack`, `builtin-approval-telegram`, `builtin-approval-whatsapp`, `builtin-approval-teams`:
    Draft (LLM) → Human (`approval.channel` = the kind) → Condition on `decision` → Polish (LLM) or End.
  - `builtin-approval-email`: Draft → Human (`email`) → Condition → Send email with the result → End.
  - `builtin-approval-multilevel`: Draft → Human (team lead, `slack`) → Condition → Human (manager, `email`) →
    Condition → End.
  - `builtin-support-escalation`: Retriever → LLM answer → Decision (confident?) → End, or Human review → End.
  - `builtin-batch`: For each over a list field → LLM summary per item → joined result → End.
  - Each Human node's `approval` holds only `channel`. No `channel_id`, `target` or `approvers`.
- **Frontend.**
  - Built-in names and descriptions come from locale keys `templates.builtin.<id>.name` and `.description`, for all
    12 built-ins. Other templates show the API's name and description.
  - `template-gallery.tsx`: each card shows the `ChannelLogo` of every distinct `approval.channel` in the template's
    Human nodes, next to the name.
- **Tests.**
  - `tests/test_templates.py`: the 12 IDs in order. Every built-in validates. Channel templates hold only the kind.
    Each one runs in mock mode up to its Human node, or to the end for `builtin-batch`.
  - Frontend: unit test for the channel-kind extraction; e2e for the gallery (12 cards, logos on channel cards, the
    Vietnamese name when the UI is in Vietnamese).
- **Docs.** `handbook/docs/*/guide/templates.md` lists the new templates. Retake `templates.png` (en, vi).

### Out Of Scope

- Translating saved or imported templates.
- Template categories, search or marketplace.
- Changes to channel sending or to the template API.

## Inputs

- REQ-0040, REQ-0015 (TASK-0025), REQ-0035 (For each), REQ-0036 (Decision), REQ-0037 (Send email).
- `ChannelLogo` from TASK-0063.

## Related Artifacts

- Requirements: `.factory-state/artifacts/REQ-0040-channel-templates-and-logos.md`,
  `.factory-state/artifacts/REQ-0015-template-library.md`
- Design: none
- Architecture: `docs/backend-architecture.md` (DEC-0009)
- Decisions: DEC-0008, DEC-0042 (from TASK-0063)
- Discovery: `ApprovalService.on_waiting` skips sending when a needed target is missing; `ChannelService.for_node`
  uses the owner's connection of the kind when only `channel` is set.
- Clarifications: none

## Expected Outputs

- 8 new built-ins in `templates.py`
- Locale keys `templates.builtin.*` in `en.json` and `vi.json`
- Gallery card logos
- Tests and handbook updates

## Implementation Notes

- Keep prompts short and runnable on the offline mock. Lay nodes out left to right like the existing built-ins.
- Read channel kinds from `workflow.nodes[].data.approval.channel` on the client. No API change.
- Keep `BUILTIN_IDS` the single source of truth for which templates are built-in.

## Constraints

- No raw SQL and no schema change. Backend layers unchanged.
- shadcn and theme tokens. en/vi keys identical.
- Templates run in mock mode with no API key and no channel connected.

## Dependencies

- TASK-0063 (`ChannelLogo`) must be merged first.

## Acceptance Criteria

- `GET /api/templates` lists the 12 built-ins in order, and all of them pass the validator.
- Creating from each new template gives a workflow that runs in mock mode, up to the first Human node or to the end.
- Channel templates store only `approval.channel`.
- All 12 built-in names and descriptions show in en and vi.
- Gallery cards show the logos of their channels: one for each channel template, two for the two-level template.
- Backend tests pass on SQLite and Postgres 17 + Redis 7. Frontend build, lint, vitest and e2e pass. The handbook
  builds in en and vi.

## Validation Plan

- `pytest tests/test_templates.py`, then the full backend suite on SQLite and Postgres.
- Vitest for the channel-kind helper. E2E for the gallery in en and vi.
- Manual: create a workflow from the Slack template, run it, approve in the studio.

## Assumptions

- The Decision and For each nodes behave as their REQs describe.

## Open Questions

- None.

## Activity Log

- 2026-10-20: planned from REQ-0040.
- 2026-10-21: implemented. Two changes beyond the plan, both in REV-0058:
  - template summaries gain a `channels` field;
  - `sanitize` now keeps only a Human node's channel kind.

## Handoff Notes

- Next: owner review of the PR, then merge. REQ-0040 is complete after this task.
