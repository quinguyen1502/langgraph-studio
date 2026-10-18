# Decision Record

## Metadata

- Project: langgraph-studio
- Decision ID: DEC-0002
- Status: Superseded by DEC-0033 (2026-10-18)
- Owner: Thái Quí Nguyễn
- Created: 2026-10-16
- Updated: 2026-10-18
- Related Requirements: REQ-0001
- Related Architecture: ARCH-0001
- Related Tasks: TASK-0002

> Superseded by DEC-0033: the integration branch is `develop`. The text below is the 2026-10-16 decision.

## Context

Repository was created with a single `main` branch; framework default is `develop`.

## Decision

Integration branch is main. `main` is the integration branch (`integration_branch: main`). Task branches `factory/task-<id>-<slug>` branch from and open PRs into `main`. No `develop` branch.

## Rationale

Approved by the owner on 2026-10-16 after reviewing the onboarding proposals (TASK-0001 open questions).

## Alternatives Considered

- Option: Introduce develop
  - Benefits: Framework default
  - Tradeoffs: Extra branch for a solo internal project
  - Reason Not Chosen: Owner preference

## Impacts

- CI triggers on push/PR to main

## Risks

- Low; decision is reversible.

## Approval

- Approved By: Thái Quí Nguyễn (owner)
- Approved On: 2026-10-16
- Scope And Limits: langgraph-studio repository

## Review Or Revisit Trigger

- Revisit if release staging becomes necessary.
