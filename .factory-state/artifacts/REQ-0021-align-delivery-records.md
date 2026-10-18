# Requirement

## Metadata

- Project: langgraph-studio
- Requirement ID: REQ-0021
- Status: Implemented
- Owner: Thái Quí Nguyễn
- Created: 2026-10-18
- Updated: 2026-10-18
- Source: owner request 2026-10-18 to plan and handle the leftover records, excluding the GitHub Actions quota.

## Summary

Make the factory records match work that is already merged to `develop`, and record that the integration branch is `develop`.

## Problem Or Opportunity

REQ-0002 through REQ-0018 still say Proposed after their tasks were merged. DEC-0002 and `factory.yaml` still say the integration branch is `main`, while task pull requests land on `develop`.

## Scope

### In Scope

- Set REQ-0002, REQ-0003, REQ-0004, REQ-0005, REQ-0006, REQ-0007, REQ-0008, REQ-0010, REQ-0011, REQ-0012, REQ-0013, REQ-0014, REQ-0015, REQ-0016, REQ-0017, and REQ-0018 to Implemented, each pointing at its done task. Do not rewrite their scope.
- Supersede DEC-0002 with a new decision: the integration branch is `develop`.
- Set `integration_branch` in `.factory-state/factory.yaml` to `develop`.
- Add `develop` to the push branches of `.github/workflows/factory-verify.yml`. `ci.yml` already lists `develop`.

### Out Of Scope

- GitHub Actions billing or quota.
- Product code, tests, and the editor leftovers (fold tooltip, `spliceNode` tests).
- Per-node input schema, `Command`, and `Send`.
- Sandbox follow-ups accepted in QA-0029.
- Rewriting the body of DEC-0002 or retargeting historical pull requests.

## Stakeholders Or Users

- Thái Quí Nguyễn, reading the factory board
- The next agent that opens a task branch

## Current Context

- Integration pull requests since the phase re-plan merge into `develop`.
- DEC-0002 (Accepted 2026-10-16) says there is no `develop` branch.
- `.factory-state/factory.yaml` has `integration_branch: main`.

## Desired Behavior

- A reader can trust Requirement status and the integration branch without checking git history.
- New task branches still start from `develop` and open pull requests into `develop`.

## Business Rules

- An old accepted decision is superseded by a new decision. Its original decision text stays.

## Constraints

- No product source edits in this requirement.
- `main` stays as history.

## Acceptance Criteria

- Each listed requirement has Status Implemented and a link to its task file under `.factory-state/tasks/done/`.
- DEC-0002 is Superseded by the new decision. The new decision states that the integration branch is `develop`.
- `factory.yaml` has `integration_branch: develop`.
- `factory-verify.yml` runs on push to `develop` as well as `main`.

## Edge Cases

- REQ-0009, REQ-0019, and REQ-0020 are already Implemented. Leave them.

## Assumptions

- The owner approved this record pass on 2026-10-18. `factory ready` does not exit 0 on this machine. The owner asked to proceed with the leftover plan anyway.
- One task, because the edits are records only.

## Open Questions

- None

## Related Artifacts

- `.factory-state/decisions/DEC-0002-integration-branch-main.md`
- `.factory-state/decisions/DEC-0033-integration-branch-develop.md`
- `.factory-state/tasks/done/TASK-0033-align-delivery-records.md`
- `.factory-state/artifacts/REV-0032-task-0033.md`
- `.factory-state/artifacts/QA-0032-task-0033.md`
- `roadmap.md`
