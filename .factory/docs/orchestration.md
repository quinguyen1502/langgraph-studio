# Multi-Tool Orchestration

`factory orchestrate` dispatches independent tasks to multiple AI coding tools in
parallel. It is a **dispatch-and-supervise** boundary: Factory prepares an isolated
git worktree, a task branch, and a context brief for each task, then hands control to
the assigned tool and the human owner. It does not write application code, open pull
requests, or merge anything.

## Model

- **One tool per task.** Tasks currently in `todo` are assigned to enabled, installed
  tools round-robin. Each task keeps exactly one branch and, later, one pull request.
- **Isolated git worktrees.** Each task gets its own worktree under
  `.factory-state/orchestration/worktrees/<branch>` checked out on a new branch
  `factory/task-<id>-<slug>` based on the integration branch. Worktrees never contend
  on the main index.
- **File-based handoff.** Each worktree receives an `ORCHESTRATION-BRIEF.md` with the
  task id, title, branch, integration branch, task artifact path, and related artifacts
  so any tool or person has enough context without chat history. The brief is local-only.

## Commands

```bash
factory orchestrate plan -C project        # preview assignments; read-only
factory orchestrate run -C project          # create worktrees, write briefs, move tasks to doing
factory orchestrate status -C project       # show recorded worktrees and tools
factory orchestrate validate -C project     # check state against live worktrees
factory orchestrate cleanup -C project      # remove clean factory-created worktrees
```

Useful flags:

- `--tool <id>` (repeatable) overrides the tool set; defaults to enabled tools in
  `factory.yaml` that are also installed.
- `--max-parallel N` bounds concurrent setup (default 2).
- `--launch` (on `run`) starts each tool session in its worktree. Without it, `run`
  prints ready-to-run launch commands instead.
- `--yes` (on `run`) skips the interactive review.
- `--force` (on `cleanup`) removes worktrees even with uncommitted changes.

## Safety boundaries

- Only tasks in `todo` are dispatched, and only the `todo -> doing` transition is made.
- No pull requests are created and nothing is merged or force-pushed; delivery stays in
  the normal developer flow.
- `cleanup` removes only factory-created worktrees that are clean unless `--force`.
- If an assignment fails mid-setup, its worktree and branch are rolled back and the
  failure is recorded in `.factory-state/orchestration/INCOMPLETE` for retry.
- Factory never touches home-directory configuration, credentials, model selection, or
  provider endpoints. Write permissions inside a session are governed by the project's
  tool kit, not by the orchestrator.

## State

```text
.factory-state/orchestration/
├── active.yaml            # schema version, per-task tool/branch/worktree records
├── INCOMPLETE             # present only after a partial run; resolve and rerun
└── worktrees/             # local-only task checkouts (git-ignored)
```
