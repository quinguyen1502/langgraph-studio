# Factory pipeline

Every Factory project moves through the same set of milestones. Each stage
leaves a durable marker under `.factory-state/`, so tools (and the
interactive shell) can tell where a project stands without asking. This
page names the milestones, explains what each one produces, and points to
the commands that drive them.

Run `/pipeline` inside `factory shell` for the same information as a live
table with your current project's status.

## Milestones

```
 ┌──────┐    ┌──────────┐    ┌─────────┐    ┌────────┐    ┌────────────┐    ┌───────┐
 │ Init │ ─▶ │ Scaffold │ ─▶ │  Deps   │ ─▶ │ Verify │ ─▶ │ Stack conf │ ─▶ │ Tasks │
 └──────┘    └──────────┘    └─────────┘    └────────┘    └────────────┘    └───────┘
     required        optional        optional      optional         optional        checkpoint
```

Scaffold, Deps, Verify, and Stack config are optional in the sense that a
project can skip them if it does not need them (e.g. a docs-only project
skips Scaffold; a service that runs in Kubernetes skips Docker Compose).
They are however the recommended path from an empty repository to a
project ready for task work.

### 1. Init  ·  `factory init <name>` (or `factory import`)

Creates the artifact bundle — `AGENTS.md`, `project.md`, `vision.md`,
`roadmap.md`, `project-specs.md`, `.factory-state/`, an initial discovery
task, and a project-local tool policy. Register the project in the global
registry so `factory shell` can find it. Init is not the implementation
gate; run `factory ready` after discovery, requirements, and planning.

Marker: `.factory-state/factory.yaml`. Docs: [`cli.md`](cli.md#project-initialization).

### 2. Scaffold  ·  `factory scaffold plan|apply|validate`

Generates the source baseline for approved stack choices (React, Next.js,
Django, FastAPI, Go with Gin, Flutter, and more). Runs in a staging
directory, previews all output, preserves existing conflicts as
proposals, and records managed hashes.

Marker: `.factory-state/scaffolding/generated.yaml`. Incomplete:
`.factory-state/scaffolding/INCOMPLETE`. Docs: [`scaffolding.md`](scaffolding.md).

### 3. Dependencies  ·  `factory deps plan|apply|validate`

Installs project-local dependencies from the manifests / lockfiles the
scaffold produced (or the ones the owner brought in). Never installs
adapter prerequisites globally. A failed install preserves the scaffolded
source and records an `INCOMPLETE` marker for retry.

Marker: `.factory-state/dependencies/installed.yaml`. Incomplete:
`.factory-state/dependencies/INCOMPLETE`. Docs: [`dependencies.md`](dependencies.md).

### 4. Verify  ·  `factory verify plan|run|validate`

Runs the deterministic project checks discovered from manifests — test,
lint, typecheck, framework-check, build — and stores hashed evidence.
Rejects source drift after review. This is where a project earns the
right to be dispatched to AI tools.

Marker: `.factory-state/verification/latest.yaml`. Docs: [`verification.md`](verification.md).

### 5. Stack config  ·  `factory stack plan|apply|validate`

Publishes CI (GitHub Actions or GitLab CI) and — when Docker Compose is
approved — a compose file for the chosen database. Configurators derive
from explicitly `Approved` decisions and preserve existing configuration
as review proposals.

Marker: `.factory-state/configuration/generated.yaml`. Incomplete:
`.factory-state/configuration/INCOMPLETE`. Docs: [`stack-configuration.md`](stack-configuration.md).

### 6. Tasks  ·  `factory task create|move|archive`, `factory board`

Once the pipeline is set up, day-to-day work moves through the lifecycle:

```
backlog  ─▶  todo  ─▶  doing  ─▶  review  ─▶  qa  ─▶  done
```

Dispatch `todo` tasks to AI tools in parallel via
`factory orchestrate plan|run`, watch progress on `factory board`, and
track token cost with `factory usage record` + `factory dashboard`.

Docs: [`task-lifecycle.md`](task-lifecycle.md), [`orchestration.md`](orchestration.md),
[`kanban-board.md`](kanban-board.md), [`metrics-and-budget.md`](metrics-and-budget.md).

## How `/pipeline` decides status

- **● Done** — the stage's marker file exists and no `INCOMPLETE` sits
  alongside it.
- **◐ In progress** — an `INCOMPLETE` marker exists (either alone,
  meaning the `apply` failed halfway; or next to the marker, meaning
  proposals still need review).
- **○ Not started** — no marker at all.

The **Tasks** stage is a checkpoint rather than a build phase: any task
counts as *in progress*, and only when every task is in `done` does the
row read *done*.

`/pipeline` also names the next action to run — the earliest stage that
is `in progress` if any, otherwise the earliest `not started` stage,
skipping optional stages that a later required stage has already
overtaken.
