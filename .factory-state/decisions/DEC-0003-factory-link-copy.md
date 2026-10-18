# Decision Record

## Metadata

- Project: langgraph-studio
- Decision ID: DEC-0003
- Status: Accepted
- Owner: Thái Quí Nguyễn
- Created: 2026-10-16
- Updated: 2026-10-16
- Related Requirements: REQ-0001
- Related Architecture: ARCH-0001
- Related Tasks: TASK-0002

## Context

sw-ai-factory is private; a submodule would require framework access for every clone and CI run.

## Decision

Factory linked as a copy. Keep `.factory/` as a vendored copy (`factory_link_mode: copy`). Updates are done by re-running `factory import` from a newer framework checkout.

## Rationale

Approved by the owner on 2026-10-16 after reviewing the onboarding proposals (TASK-0001 open questions).

## Alternatives Considered

- Option: Git submodule
  - Benefits: Easy pinning/updates
  - Tradeoffs: Private-repo credentials in CI and for every collaborator
  - Reason Not Chosen: Owner preference

## Impacts

- `.factory/` is committed (larger diff on framework upgrades)

## Risks

- Low; decision is reversible.

## Approval

- Approved By: Thái Quí Nguyễn (owner)
- Approved On: 2026-10-16
- Scope And Limits: langgraph-studio repository

## Review Or Revisit Trigger

- Revisit if the framework becomes public or CI gets a deploy key.
