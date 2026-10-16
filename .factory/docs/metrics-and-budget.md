# Metrics, Costs, And Token Budgets

Factory dispatches work to external AI coding tools and never calls provider APIs itself, so
token counts and costs are recorded explicitly. This keeps metrics provider-neutral and works
regardless of which tool ran a task.

## Recording Usage

```text
factory usage record -C project \
  --scope task --ref TASK-0001 --tool claude-code \
  --in 1200 --out 800 --cost 0.03 [--note "first pass"]
```

- `--scope` is `task` or `agent`.
- `--ref` is the task ID (for `task` scope) or the agent role (for `agent` scope).
- `--in` / `--out` are input/output token counts; `--cost` is USD.

### Capturing usage from a coding tool

`factory usage capture` parses the JSON output of a coding tool and records one entry. Run the
tool with its JSON output format and pipe it in (or pass `--from FILE`):

```text
codex exec --json "…"            | factory usage capture --tool codex  --ref TASK-0001
claude -p --output-format json … | factory usage capture --tool claude --ref TASK-0001
cursor-agent -p --output-format json … | factory usage capture --tool cursor --ref TASK-0001
factory usage capture --tool claude --ref TASK-0001 --from run.json
```

The parser scans the output for the well-known token/cost keys (`input_tokens`/`prompt_tokens`,
`output_tokens`/`completion_tokens`, `total_cost_usd`/`cost_usd`) and, for streaming JSONL,
takes the final cumulative totals — so it works for Codex, Claude Code, Cursor, and Grok without a
brittle per-tool schema. Tool names are normalized (`claude` → `claude-code`,
`grok` → `grok`). It does not
auto-attach to `factory orchestrate` (those sessions are human-driven and detached); you pipe a
tool's output to `capture`, or wrap the tool in a small script that does.

### Bulk import

To load many records at once, write them to a JSONL or CSV file and import:

```text
factory usage import usage.jsonl -C project
factory usage import usage.csv -C project
```

CSV columns are `scope,ref,tool,in,out,cost[,note]` (with `tool_id`/`input_tokens`/
`output_tokens`/`cost_usd` also accepted); JSONL rows are objects with the same fields.

Records are stored through the project's storage backend: appended to
`.factory-state/metrics/usage.yaml` for the `folder` backend, or a `usage` table in the
database for the `folder+sqlite` and `folder+postgres` backends. With `folder+postgres`, a
shared Postgres instance lets a whole team aggregate token and cost across their clones,
while task documents stay in git as the source of truth.

## Reporting

```text
factory usage list -C project --by ref      # by task/agent
factory usage list -C project --by tool
factory usage list -C project --by budget
factory dashboard -C project                # TUI; prints text when not a terminal
```

The `factory dashboard` TUI has three layers:

1. **KPI cards** — total tokens, total cost, entries, today's tokens (with a Δ vs yesterday),
   this week's tokens (Δ vs last week), and the number of over-budget keys (red alert card
   when non-zero).
2. **Comparison charts** — rendered with [`textual-plotext`](https://pypi.org/project/textual-plotext/):
   a tokens trend you can switch between **day / week / month** with `t`, tokens by tool, cost
   per 1K tokens by tool, input vs output by tool, and a budget-burn (% of limit) chart.
3. **Detail tables** — by task/agent, by tool, by day, and budgets, each with a `TOTAL` row.

Keys: `r` refresh, `t` cycle the trend granularity (day → week → month), `q` quit. Over-budget
rows and negative remaining values are highlighted in red. Time buckets are UTC (weeks are ISO
weeks).

`textual-plotext` (which pulls the pure-Python `plotext`, no numpy) is a normal dependency, so
it works on every supported Python. If it is somehow unavailable, the dashboard falls back to
Unicode bar charts. The non-interactive `factory dashboard` (no TTY) prints the same summary,
charts, and tables as text.

## Token Budgets

Budgets are token limits keyed by scope:

```text
factory budget set task:TASK-0001 100000 -C project
factory budget set agent:developer 500000 -C project
factory budget list -C project
factory budget remove task:TASK-0001 -C project
```

Budgets are stored in `.factory-state/factory.yaml` under `budgets`, and the enforcement mode
is `budget_enforcement` (`warn` by default, or `block`).

### Enforcement During Orchestration

When `factory orchestrate plan` or `run` evaluates a `todo` task, it compares recorded usage
for `task:<id>` against any configured budget:

- `warn`: the task is still assigned, and a warning is added to the plan.
- `block`: the task is dropped from the plan with a "Blocked" warning, so no worktree is
  created for it. Other tasks proceed normally.

This matches Factory's dispatch-and-supervise model: budgets shape what gets dispatched but
never modify or merge application code.
