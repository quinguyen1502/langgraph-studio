# Factory shell (interactive REPL)

`factory shell` opens a REPL that exposes every `factory` subcommand
through a fuzzy autocomplete, per-action argument forms, and confirmation
gates on destructive commands — without requiring you to memorize command
names or flags. Running `factory` with no arguments in a terminal drops
into the same REPL; non-interactive contexts (pipes, CI) keep the
traditional CLI behavior.

Under the hood the shell is
[`prompt_toolkit`](https://python-prompt-toolkit.readthedocs.io/) for input
and [`rich`](https://rich.readthedocs.io/) for output — the same
combination `pgcli`, `mycli`, and the `claude`/`codex` CLIs use. The shell
never re-implements business logic: read-only commands dispatch as a
captured subprocess (`python -m factory_cli …`), while interactive
commands hand the parent terminal over so their own Textual UIs render
without nesting.

## Starting

```bash
factory                      # bare invocation in a TTY drops in
factory shell                # explicit
factory shell -C ./demo      # preselect a project by path
factory shell --project demo # preselect a registered project by name
```

## Prompt syntax

At the `factory>` prompt you can:

- **Type an action name** — `board`, `dashboard`, `orchestrate.plan`,
  `task.create`, `usage list`. Aliases (`kanban` → board, `dispatch` →
  orchestrate.run) resolve too.
- **Type a slash command** — always starts with `/`.
- **Press Tab** — fuzzy completion over every action id, every alias, and
  every slash command.
- **Ctrl+R** — reverse history search (prompt_toolkit).
- **Up / Down** — walk history.
- **Ctrl+D** — leave the REPL.

### Slash commands

| Command | What |
| --- | --- |
| `/help` | Show slash commands and general keybinds. |
| `/tour` | Reshow the first-run onboarding panel (5 quick steps). |
| `/pipeline` | Show Factory milestones and where this project stands. See [`pipeline.md`](pipeline.md). |
| `/status` | Reprint the current project overview. |
| `/refresh` | Recompute the overview from disk. |
| `/projects` | List every registered project. |
| `/project <name>` | Switch to a registered project. |
| `/quit` / `/exit` | Leave the REPL (Ctrl+D also works). |

### First-run tour

On first entry the REPL prints a five-step onboarding panel (Discover /
Run / Fill in / Confirm / Leave) so newcomers do not have to read
`docs/shell.md` first. Dismissal is persisted in
`~/.factory/shell-state.yaml` (respecting `FACTORY_HOME` /
`XDG_CONFIG_HOME`). Run `/tour` any time to see it again.

## Action dispatch

Every action falls into one of four routes, decided from its declared
`ActionKind` and (for terminal-owning cases) its id:

- **READ** — runs as a captured subprocess; stdout/stderr are printed in
  the same terminal, the REPL stays open. Example: `usage list`,
  `orchestrate.status`, `validate`.
- **MUTATING with a form** — collect required arguments through sequential
  prompts (with validation for `INT` and `CHOICE` fields), preview the
  exact `factory …` argv, and require a `y`/`yes` confirmation before
  running. Example: `task.create`, `budget.set`, `usage.record`.
- **MUTATING without a form** — jump straight to the confirmation preview.
- **Terminal-owning** (`init`, `import`, `specs`, `clarify`,
  `tools.configure`, `tools.apply`, `scaffold.apply`, `deps.apply`,
  `stack.apply`, `orchestrate.run`, `board`, `dashboard`) — the shell
  invokes the child without capturing so its own Textual review flow can
  render, then re-prints the prompt when the child returns.

## Coverage

Every top-level `factory` subcommand has a matching `Action`, enforced by
`tests/test_shell.py::ActionRegistryTests`. Every subcommand with required
arguments has a matching form spec, enforced by
`RequiredArgsHaveFormsTests` — a new required-arg subcommand will fail CI
until its form is declared.

## Non-interactive fallback

`factory shell` on a pipe or in CI prints the standard help and exits with
code 0. Bare `factory` in the same environment behaves the same way.

## History

Command history persists to `~/.factory/shell-history` (or under
`$FACTORY_HOME` / `$XDG_CONFIG_HOME/factory/`).

## Design rationale

An earlier design used a full-screen Textual TUI. It was retired because:

1. Users came from `claude` / `codex` CLIs and expected a REPL, not a
   full-screen app that replaces the scrollback.
2. Nested Textual apps (opening the board from inside the hub) required
   an exit-and-re-open dance that never quite matched a normal terminal.
3. Rich markup in status strings (`[/]`, `[n]`) required constant escape
   discipline and produced runtime crashes when a new label slipped
   through.
4. Testing required either mocking Textual internals or driving a virtual
   terminal; the REPL is a plain object with unit tests that run in <1s.

The shell keeps the reusable schema from that design — `Action` registry,
`FORM_SPECS`, `ShellContext`, subprocess runner — because those are
independent of the UI shell and remain valid seams if a future
natural-language chat mode is ever added.
