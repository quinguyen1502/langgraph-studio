---
name: scoped-change
description: Make a small, scoped implementation or review-feedback fix then stop before validation so the user can review. Use when the user asks to implement or fix a specific change without running tests, formatters, analyzer, or other validation.
---

# Scoped Change

Apply the requested change with the smallest real implementation or fix that satisfies it. Stop before validation so the user can review the diff.

## When to use

- Implementing a small UI or logic change the user just described.
- Applying review-feedback fixes on the active task branch.
- Any "just do this, I'll validate after" request.

Do not use this skill when the user asks for validation, testing, formatting, analysis, review, or QA. Use `task-validation`, `task-review`, `task-qa`, or `finish-pr` for those.

## Rules

- Make the smallest real implementation or fix that satisfies the request. Preserve unrelated user changes.
- Do not add or update tests unless the user explicitly asks.
- Do not run tests, analyze, build, format, or other validation commands unless the user explicitly asks. See `task-validation` when the user is ready to validate.
- Do not create fake or placeholder functionality for real feature requests. If real implementation is blocked, report the blocker and fallback options instead.
- If adding a package, plugin, or library is necessary, first verify it against the project's dependency selection standard at `.factory-state/standards/dependencies.md` covering stability, maintenance, provenance, status, platform support, license, and necessity. If no project standard exists, use `.factory/templates/standards/dependencies-template.md` as the shape and ask the owner to instantiate it before adding the dependency.

## Task and branch context

- If the change belongs to an unfinished Factory task, keep it on the active task branch and update the active task artifact instead of creating a new task, branch, requirement, review, or QA artifact.
- Update the active task activity log only when project standards require the change to be recorded.
- If no task is active and the change is not trivial, ask the user whether to start a task first with `task-start`.

## Reporting

- After the change, summarize the affected behavior and files.
- State clearly that tests and validation were not run pending user confirmation.
- If the change addresses a specific reviewer finding, mention which finding it resolves.
