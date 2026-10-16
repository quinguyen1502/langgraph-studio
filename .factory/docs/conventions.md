# Conventions

These conventions apply to the factory framework and may be copied or adapted by project repositories.

## Framework Repository

- Keep only reusable assets in this repository.
- Do not add project implementations, sample applications, or domain-specific examples.
- Do not assume a language, framework, architecture, database, hosting platform, or business domain.
- Keep templates generic and artifact-driven.

## Project Repositories

- Store project-specific context in the project repository, not in the factory repository.
- Use `.factory/` to consume reusable factory assets: agents, workflows, templates, and docs.
- Use `.factory-state/` for project-owned generated workflow state.
- Keep project standards, decisions, tasks, and artifacts under `.factory-state/`.
- Keep source and tests in project-defined locations.
- Document any project-specific deviations from factory guidance.

## Artifact Naming

Default names may be adapted by each project:

- Requirements: `REQ-0001-title.md`
- Discovery: `DISC-0001-title.md`
- Plans: `PLAN-0001-title.md`
- Design: `DES-0001-title.md`
- Architecture: `ARCH-0001-title.md`
- Tasks: `TASK-0001-title.md`
- Reviews: `REV-0001-task-id.md`
- QA: `QA-0001-task-id.md`
- Decisions: `DEC-0001-title.md`
- Completion summaries: `SUM-0001-title.md`

## Code Comments

Language-neutral, and enforced at review rather than by tooling: none of the
failures below is caught by a formatter, a linter, or a test suite. They are
only visible to a reader.

A comment earns its place by changing what a maintainer does. Everything else
is noise that ages badly.

### Write

- **Describe the code, not the session.** The most common failure in
  agent-written code is a comment recording what was found and decided while
  working — an incident, a date, a task id. That is a diary entry. Keep the
  constraint the incident taught; drop the event. "This API identifies a file
  by its path" is the rule. "Found on a device after 2.66 GB had been fetched"
  is how the rule was learned, and belongs in the task's activity log.
- **State a cross-cutting reason once**, on the type or function that owns the
  decision. Copies drift into slightly different claims, and a reader who
  finds one has no way to know it is not the authoritative version.
- **Do not assert the current state of the project.** "Not implemented yet",
  "never compiled", "the list is empty" — these go stale silently, and a
  confidently wrong comment is worse than none. Prefer what the code
  guarantees.
- **Do not stamp provenance.** A task id means nothing to someone reading the
  code, and the history is already in version control and in the workflow
  state. Reference a standing decision when a reader may have to go and check
  it; do not reference the task that added the line.
- **Date a figure only when it must be re-measured.** A measurement a
  standard forbids estimating is worth its date. Nothing else is.
- **Comments in tests are exempt from the incident rule** where the incident
  is why the test must not be simplified — a fixture that would stop
  exercising a rule, or a known boundary recorded as an open question.

### Review

The four checks a reviewer runs against each comment in a diff:

1. Is it describing the code, or the session?
2. Is the same reason stated more than once across files?
3. Does it assert a project state that will go stale?
4. Would a maintainer break something without it? If not, it restates.

**A change that deletes comments in bulk is audited mechanically, never from
the author's list of what mattered.** That list is written by the same memory
that did the cutting and will omit exactly what was forgotten. Extract every
figure and identifier from the deleted lines, subtract what the added lines
contain, and check the remainder against the tree.

## Agent Handoffs

- Every handoff must be file-based.
- Every artifact must identify related inputs.
- Every assumption must be documented.
- Every blocked item must identify the missing decision, artifact, or approval.
