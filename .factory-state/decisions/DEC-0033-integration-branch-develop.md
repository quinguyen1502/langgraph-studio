# Decision Record

## Metadata

- Project: langgraph-studio
- Decision ID: DEC-0033
- Status: Accepted
- Owner: Thái Quí Nguyễn
- Created: 2026-10-18
- Updated: 2026-10-18
- Related Requirements: REQ-0021
- Related Architecture: ARCH-0001
- Related Tasks: TASK-0033

## Context

DEC-0002 (2026-10-16) set the integration branch to `main` and said there would be no `develop` branch. Delivery since the phased re-plan has branched from `develop` and opened pull requests into `develop`. `.factory-state/factory.yaml` still says `integration_branch: main`.

## Decision

The integration branch is `develop`. Task branches `factory/task-<id>-<slug>` start from `develop` and open pull requests into `develop`. `main` stays as history and is not the target of new task pull requests. Supersedes DEC-0002.

## Rationale

The record should match the branch that already holds the merged phases. Rewriting the 2026-10-16 decision text would hide the earlier choice.

## Alternatives Considered

- Option: Keep DEC-0002 and move future pull requests back to `main`
  - Benefits: The accepted decision stays literally true
  - Tradeoffs: Rewinds the branch the owner has been merging into
  - Reason Not Chosen: The owner asked to align the records with current delivery

## Impacts

- `integration_branch` in `.factory-state/factory.yaml` is `develop`
- `.github/workflows/factory-verify.yml` push branches include `develop`. `ci.yml` already triggers on `develop`
- This does not restore GitHub Actions minutes

## Risks

- Low. The change records current practice.

## Approval

- Approved By: Thái Quí Nguyễn (owner), by approving the leftover plan on 2026-10-18
- Approved On: 2026-10-18
- Scope And Limits: langgraph-studio repository. Does not retarget historical pull requests.

## Review Or Revisit Trigger

- Revisit if release staging needs a branch other than `develop`.

## Addendum 2026-10-19

The owner asked to bring `main` up to date (remaining-work item 1). `main` now receives release merges from `develop` (PR #46, `develop` → `main`, 2026-10-18). Task pull requests still target `develop`; GitHub's default branch is still `main` (a repository setting, unchanged).
