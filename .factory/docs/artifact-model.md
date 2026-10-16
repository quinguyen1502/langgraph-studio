# Artifact Model

Agents communicate by creating and updating files. Every artifact must be understandable without relying on conversation history.

Project-owned factory state lives under `.factory-state/`. Reusable framework assets live under `.factory/`.

## Artifact Types

- Requirement artifacts describe outcomes, scope, constraints, assumptions, and acceptance criteria.
- Design artifacts describe user flows, interaction states, content, accessibility, responsive behavior, and UX acceptance criteria.
- Architecture artifacts describe structure, decisions, rationale, tradeoffs, and impact.
- Task artifacts describe executable work, dependencies, lifecycle state, implementation notes, and validation expectations.
- Review artifacts describe review scope, findings, and review decision.
- QA artifacts describe validation scope, evidence, results, gaps, and QA decision.
- Decision records capture important choices that need durable context.
- Standards files describe project-specific conventions discovered or approved for the project.
- Discovery artifacts describe observed project context, stack evidence, commands, gaps, and open questions.
- Clarification artifacts batch larger, grouped, checklist, or conditional owner questions and preserve submitted answers for later propagation into source artifacts.

Artifacts should represent durable project knowledge and delivery state. Do not create standalone project tasks, blockers, review artifacts, or QA artifacts solely for assistant mechanics such as trying a command, discovering missing local authentication, retrying after sandbox or network restrictions, or reporting transient tooling failures. Record those issues in the active task only when they materially affect that task; otherwise summarize them in the owner-facing response.

## Default Locations

- Requirements, discovery, design, architecture, review, QA, and completion summaries: `.factory-state/artifacts/`.
- Decision records: `.factory-state/decisions/`.
- Project standards: `.factory-state/standards/`.
- Lifecycle task artifacts: `.factory-state/tasks/backlog/`, `.factory-state/tasks/todo/`, `.factory-state/tasks/doing/`, `.factory-state/tasks/review/`, `.factory-state/tasks/qa/`, and `.factory-state/tasks/done/`.
- Archived finished work: `.factory-state/archive/tasks/` and `.factory-state/archive/artifacts/`. `factory gc` (or `factory task archive`) moves old `done` tasks and companion `REV` / `QA` / `SUM` records here. Files stay in git; IDs stay reserved. Do not scan the archive when gathering context for new work.

## Reading Strategy

Agents should not read every file under `.factory-state/artifacts/` by default. The artifacts directory is durable project memory and is expected to grow over time.

Use this order when gathering context:

1. Read `vision.md`, `project.md`, `roadmap.md`, and the current task artifact.
2. Read artifacts, decisions, and standards directly referenced by the current task or requested work.
3. Read discovery artifacts or standards only when stack, commands, conventions, risk, or validation are relevant.
4. Scan `.factory-state/artifacts/` broadly only for discovery, audit, planning, migration, traceability repair, or when expected references are missing.

Artifacts and tasks should maintain explicit related artifact paths so later agents can follow references instead of scanning the whole directory.

## Movement Between Agents

1. PO creates or updates requirement artifacts in the project workspace.
2. BA refines requirements and records assumptions or open questions.
3. Designer creates or updates design artifacts when work affects users, user journeys, interfaces, CLI UX, API developer experience, or documentation experience.
4. Architect reads requirements, design artifacts when applicable, and project context, then creates or updates architecture artifacts.
5. Planner converts approved artifacts into task artifacts and places them in `.factory-state/tasks/todo/`.
6. Developer moves a task to `.factory-state/tasks/doing/`, implements work,
   updates the task, moves it to `.factory-state/tasks/review/`, and opens one
   Draft PR when remote access is available.
7. Reviewer creates a review artifact and the human owner reviews the same
   Draft PR. Passing tasks move to `.factory-state/tasks/qa/`; rejected tasks
   return to `.factory-state/tasks/doing/`.
8. QA creates a QA artifact. After owner review and QA pass, Developer updates
   final artifacts, moves the task to `.factory-state/tasks/done/`, rebases and
   squashes the task into one validated commit, then marks the existing PR
   Ready for review. Failed tasks return to `.factory-state/tasks/doing/`.
9. PO or Planner confirms higher-level requirement completion from done artifacts.

## Artifact Naming

Use stable, sortable names. A project may define its own naming convention, but the default format is:

- Requirements: `REQ-0001-title.md`
- Discovery: `DISC-0001-title.md`
- Design: `DES-0001-title.md`
- Architecture: `ARCH-0001-title.md`
- Tasks: `TASK-0001-title.md`
- Reviews: `REV-0001-task-id.md`
- QA: `QA-0001-task-id.md`
- Decisions: `DEC-0001-title.md`
- Completion summaries: `SUM-0001-title.md`

## Identifier Allocation

Sequential IDs are only unique per branch snapshot, so parallel sessions that
each take "the next free number" collide once their branches merge. Allocation
must therefore happen against every branch, not the local checkout — and not
the integration branch alone, which is blind to the sibling branch that took
the number an hour ago and has not merged yet:

- Before allocating any artifact ID, fetch, then take the next free number over
  the union of the working tree and every ref:
  `git fetch --all --prune && factory ids next TASK --all-refs`.
- An ID is taken if any file in `.factory-state/` tasks, artifacts, decisions,
  or the task archive claims it, in any lifecycle state, **on any branch**.
  Archived numbers stay retired.
- Immediately before pushing a branch that adds artifacts — and again before
  marking a PR Ready, since the last writer loses the race — re-fetch and
  confirm `factory ids next <TYPE> --all-refs` still returns the number taken.
  `factory ids check --ref origin/<integration-branch>` is the gate for
  whether the branch can land; `--all-refs` on `check` also surfaces pairs
  that were renumbered long ago on branches nobody will merge, so read the
  sources it prints beside each filename before treating one as live.
- When a collision is found, renumber the not-yet-merged allocation and its
  cross-references before pushing; the earlier-merged artifact keeps its
  number. Never renumber after merging: branch names, PR titles, and commit
  messages that carry an old ID are immutable history and keep it.
- After merging, re-run `factory ids check` on the integration branch to
  confirm the tree stayed collision-free.

## Traceability

Artifacts should reference related artifacts by ID and path. A task should identify its source requirements, design artifacts when applicable, and architecture artifacts. Review and QA artifacts should identify the task they validate.

## Assumptions

When an agent must proceed without complete information, it must document assumptions in the artifact it updates. Assumptions that affect scope, architecture, risk, or acceptance must be returned to the responsible agent or explicitly approved.
