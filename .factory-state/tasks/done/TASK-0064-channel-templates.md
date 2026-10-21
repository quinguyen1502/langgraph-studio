# Task

## Metadata

- Project: superstep
- Task ID: TASK-0064
- Status: done (PR #84, REV-0058, QA-0058)
- Owner: Thái Quí Nguyễn
- Created: 2026-10-20
- Updated: 2026-10-21
- Requirement IDs: REQ-0040
- Design IDs: none (UX direction set in REQ-0040)
- Architecture IDs: DEC-0009

## Objective

Add 8 built-in templates for real business processes (REQ-0040 table: refund, leave, social post, large order,
expense claim, purchase request, support escalation, feedback digest). Show built-in template names in en and vi. (Logos on
gallery cards were built, then removed at the owner's request on 2026-10-21.)

## Scope

### In Scope

- **Backend, `backend/app/engine/templates.py`.** Eight new entries in `BUILTINS`, after the four existing ones:
  - The eight processes in the REQ-0040 table, with the channels listed there.
  - Each Human node's `approval` holds only `channel`. No `channel_id`, `target` or `approvers`.
- **Frontend.**
  - Built-in names and descriptions come from locale keys `templates.builtin.<id>.name` and `.description`, for all
    12 built-ins. Other templates show the API's name and description.
- **Tests.**
  - `tests/test_templates.py`: the 12 IDs in order. Every built-in validates. Channel templates hold only the kind.
    Each one runs in mock mode up to its first Human node, or to the end for `builtin-feedback-digest`.
  - Frontend: e2e for the gallery (12 cards, no channel logos, the Vietnamese and English names).
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
- Backend tests pass on SQLite and Postgres 17 + Redis 7. Frontend build, lint, vitest and e2e pass. The handbook
  builds in en and vi.

## Validation Plan

- `pytest tests/test_templates.py`, then the full backend suite on SQLite and Postgres.
- E2E for the gallery in en and vi.
- Manual: create a workflow from the Slack template, run it, approve in the studio.

## Assumptions

- The Decision and For each nodes behave as their REQs describe.

## Open Questions

- None.

## Activity Log

- 2026-10-20: planned from REQ-0040.
- 2026-10-21: the owner asked to replace the five channel-only variants with real processes (REQ-0040 updated).
- 2026-10-21: implemented. One change beyond the plan (REV-0058): `sanitize` now keeps only a Human node's channel
  kind.
- 2026-10-21: the owner asked to remove the channel logos from template cards before merging. The `channels` field
  added to template summaries for them was removed too.

## Handoff Notes

- Merged on the owner's approval (2026-10-21). REQ-0040 is complete.
