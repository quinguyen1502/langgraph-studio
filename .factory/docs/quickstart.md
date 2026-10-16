# Quickstart (5 minutes)

Walk from an empty machine to a project ready for AI-driven task work.
Follow the steps in order; each block is a single copy-paste.

## 1. Install the CLI

```bash
git clone <factory-repository-url> sw-ai-factory
cd sw-ai-factory
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Verify it works:

```bash
factory --help
```

## 2. Create a project

`factory init` opens an interactive wizard that captures intent, scope,
tech stack, and expected commands. Pick sensible defaults; you can edit
everything later. An agent can skip the wizard:

```bash
factory init demo-project --no-interactive --preset api --from-specs ./brief.md
```

The project lands next to `sw-ai-factory/`. It contains `AGENTS.md`,
`vision.md`, `project.md`, `roadmap.md`, `project-specs.md`, and
`.factory-state/` with an initial discovery task in `backlog/`.

## 3. Open the interactive shell

The shell removes the need to memorize commands.

```bash
cd demo-project
factory shell
```

On first run you'll see a five-step onboarding panel. When it clears,
type `/pipeline` — this is the single most useful command in Factory:

```
factory> /pipeline
```

It shows six milestones — Init, Scaffold, Deps, Verify, Stack config,
Tasks — with your project's current status (● done, ◐ in progress, ○ not
started) and the next suggested action.

Type `/help` any time to see slash commands. Tab completes across every
factory subcommand.

## 4. Complete the initial discovery task

Every new project starts with `TASK-0001-confirm-project-context` in
`backlog/`. Move it forward:

```
factory> task.move
Task ID: TASK-0001
Target column [backlog/todo/doing/review/qa/done]: doing
About to run: factory task move TASK-0001 doing -C /path/to/demo-project
Confirm? [y/N]: y
```

Edit the task's Markdown file to record what you confirmed, then move it
to `review` → `qa` → `done` the same way. Convert `project-specs.md` with
the `onboard-specs` skill, then run `factory ready` before implementation.

## 5. (Optional) Scaffold real source

If the wizard's stack choices are marked `Approved`, generate the source
baseline. `/pipeline` will tell you if this stage is available.

```
factory> scaffold.plan            # preview adapters and paths
factory> scaffold.apply           # publish reviewed output
factory> deps.plan
factory> deps.apply               # asks about --allow-network first
factory> verify.plan
factory> verify.run
```

Each `plan` step is read-only; each `apply` shows a confirm modal with
the exact `factory ...` command before running.

## 6. Dispatch tasks to AI tools

Once you have real tasks in `todo`, hand them to Codex / Claude Code /
Cursor in parallel git worktrees:

```
factory> orchestrate.plan         # preview assignments
factory> orchestrate.run          # create worktrees + briefs, move to doing
factory> board                    # watch progress on the Kanban board
```

Track token cost and set budgets:

```
factory> dashboard                # KPI cards + charts
factory> usage.capture            # parse a coding tool's JSON output
factory> budget.set               # e.g. task:TASK-0002 -> 100000
```

## Where to go next

- [`shell.md`](shell.md) — full shell reference (dispatch routes, keybinds).
- [`pipeline.md`](pipeline.md) — every milestone in detail.
- [`orchestration.md`](orchestration.md) — safety model for multi-tool
  dispatch.
- [`metrics-and-budget.md`](metrics-and-budget.md) — usage capture,
  budgets, storage backends.
- [`cli.md`](cli.md) — every subcommand and flag.

## Troubleshooting

- **`factory: command not found`** — activate the venv
  (`source .venv/bin/activate`) or run `python -m pip install -e .`.
- **Shell shows no autocomplete** — press `Tab`; it triggers the fuzzy
  completer even on empty input.
- **A stage reports "INCOMPLETE"** — a previous `apply` left proposals to
  resolve. Run the matching `validate` action to see what remains, or
  read `.factory-state/<stage>/INCOMPLETE`.
- **Textual view looks broken** — use a truecolor terminal (iTerm2,
  kitty, Alacritty, modern Terminal.app).
