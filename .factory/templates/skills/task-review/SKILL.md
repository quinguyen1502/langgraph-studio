---
name: task-review
description: Produce a Factory review artifact for the active task by reading the diff, referenced requirements, standards, and prior artifacts, then recording blocking and non-blocking findings using the review template. Use when the user asks to review the current task or the changes on the active task branch.
---

# Task Review

Perform a structured review of the active task and record findings as a Factory review artifact. Do not implement fixes in this skill; recommend them.

## Inputs

- The active task artifact and the artifacts it directly references (requirement, design, decision, plan, related standards).
- The diff of the task branch against the integration branch.
- The review template at `templates/review-template.md` in the framework.

## Steps

1. Confirm the active task and its branch. If the task is not in `doing`, `review`, or `qa`, ask the user whether to proceed.
2. Read the task acceptance criteria, applicable standards, and prior review or QA artifacts if any.
3. Read the diff against the integration branch. Focus on scope creep, missing acceptance criteria, standards violations, and risks not already documented.
4. Classify each finding as `blocking` or `non-blocking`. A blocking finding must fail the acceptance criteria, violate a required standard, or introduce material risk.
5. Allocate the review ID with `git fetch --all --prune` then `factory ids next REV --all-refs`. Write `.factory-state/artifacts/REV-<id>-TASK-<task>-<short-name>.md` using the review template. Include the diff scope reviewed, findings by classification, and explicit "no blocking findings" language when appropriate.
6. Update the task activity log per project standards if required. Do not move the task through lifecycle in this skill; that is an owner decision or the finish-pr skill.

## Non-goals

- Do not edit implementation files.
- Do not run tests, build, or other validation. Reference the task-validation skill instead.
- Do not open, close, or merge pull requests.
- Do not approve on behalf of the owner. Recommendations are advisory.
