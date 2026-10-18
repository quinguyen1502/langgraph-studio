# Decision Record

## Metadata

- Project: langgraph-studio
- Decision ID: DEC-0001
- Status: Accepted
- Owner: Thái Quí Nguyễn
- Created: 2026-10-16
- Updated: 2026-10-16
- Related Requirements: REQ-0001
- Related Architecture: ARCH-0001
- Related Tasks: TASK-0002

## Context

Factory `ready` requires a published scaffold for any Approved source stack; this repository already has source, so scaffolding would only create conflicts. CI was Proposed.

## Decision

Keep application stack Preferred; approve GitHub Actions CI. Frontend (React/Vite/@xyflow/react/Tailwind/shadcn), backend (FastAPI + langgraph), database (SQLite) and testing stay `Preferred`. CI/CD `GitHub Actions` is `Approved` and drives `factory stack` (factory-verify.yml) plus the project CI workflow `ci.yml`.

## Rationale

Approved by the owner on 2026-10-16 after reviewing the onboarding proposals (TASK-0001 open questions).

## Alternatives Considered

- Option: Approve whole stack
  - Benefits: Factory-consistent statuses
  - Tradeoffs: Forces a scaffold on an existing codebase
  - Reason Not Chosen: Would only produce conflicts/INCOMPLETE markers

## Impacts

- `factory scaffold` stays unused
- `factory stack plan` now publishes `.github/workflows/factory-verify.yml`

## Risks

- Low; decision is reversible.

## Approval

- Approved By: Thái Quí Nguyễn (owner)
- Approved On: 2026-10-16
- Scope And Limits: langgraph-studio repository

## Review Or Revisit Trigger

- Revisit if the stack changes (e.g. REQ-0008 Postgres) or Factory adds an 'existing source' scaffold marker.
