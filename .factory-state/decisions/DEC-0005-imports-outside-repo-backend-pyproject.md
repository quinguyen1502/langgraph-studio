# Decision Record

## Metadata

- Project: langgraph-studio
- Decision ID: DEC-0005
- Status: Accepted
- Owner: Thái Quí Nguyễn
- Created: 2026-10-16
- Updated: 2026-10-16
- Related Requirements: REQ-0001
- Related Architecture: ARCH-0001
- Related Tasks: TASK-0002

## Context

`factory deps/verify plan` scanned `backend/imports/` (cloned repos with their own manifests) and could not discover the backend test suite (no pyproject).

## Decision

Import workspaces outside the repo; backend pyproject.toml. Import workspaces default to `~/.langgraph-studio/imports` (override `STUDIO_IMPORT_DIR`); previously imported workflows keep absolute paths and keep working. Backend gets `backend/pyproject.toml` (dependencies, `dev` extra with pytest, pytest config); `requirements.txt` kept for compatibility. Folded into TASK-0002.

## Rationale

Approved by the owner on 2026-10-16 after reviewing the onboarding proposals (TASK-0001 open questions).

## Alternatives Considered

- Option: Keep imports in repo and patch Factory ignore list
  - Benefits: No app change
  - Tradeoffs: Requires framework change; framework must not be modified
  - Reason Not Chosen: Not allowed

## Impacts

- `factory deps plan`/`verify plan` discover only backend + frontend
- Test fixture no longer ships requirements.txt (importer falls back to installing langgraph)

## Risks

- Low; decision is reversible.

## Approval

- Approved By: Thái Quí Nguyễn (owner)
- Approved On: 2026-10-16
- Scope And Limits: langgraph-studio repository

## Review Or Revisit Trigger

- Revisit with REQ-0009 container sandbox.
