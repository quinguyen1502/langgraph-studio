# Decision

## Metadata

- Decision ID: DEC-0025
- Status: Accepted
- Date: 2026-10-17
- Related: TASK-0029, DEC-0024, docs/ui-conventions.md rule 7

## Context
Every delete in the UI must make the user type the item's name, using the shared `ConfirmDeleteDialog`. For a short time, workflow, user and team deletes also checked the typed name on the server: a `confirm_name` field, rejected with `CONFIRM_NAME_MISMATCH`.

## Decision
- The confirmation is **UI-only**, as on GitHub. The API stays a plain `DELETE`, with no `confirm_name` parameter or body field and no `CONFIRM_NAME_MISMATCH` code.
- `ConfirmDeleteDialog` and the UI rule (type the exact name, button disabled until it matches) stay as they are.

## Consequences
- API clients, scripts and tests delete without echoing the name, so there is no breaking change to the API.
- The protection is against accidental clicks in the UI. Authorization (owner/admin, `AccessService`) is still enforced on the server.
