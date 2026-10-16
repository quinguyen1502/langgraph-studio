# Kanban Board

`factory board` opens an interactive terminal board for one project's lifecycle tasks. It
requires a terminal (stdin and stdout are TTYs).

```text
factory board -C project
factory board --project demo     # resolve the project from the registry
```

## Layout

The board shows one column per lifecycle state, in order:

```text
backlog -> todo -> doing -> review -> qa -> done
```

Each column header shows its task count, and each task appears as a focusable card labeled
`<TASK-ID> · <title>`.

## Keys

| Key | Action |
| --- | --- |
| `←` / `h` | Stage a move of the focused task to the previous state |
| `→` / `l` | Stage a move of the focused task to the next state |
| `Enter` / `d` | View the focused task's full detail |
| `s` | Save — persist all staged moves to storage |
| `c` | Discard all staged moves |
| `u` | Undo the last staged move (one step) |
| `r` | Reload the board from storage (drops staged moves) |
| `q` | Quit |
| `Ctrl+T` | Toggle light/dark theme |

## Staged moves: nothing is saved until you press `s`

Moving a card with the arrow keys is **staged in memory only** — storage is not touched yet.
A staged card is marked with a leading `•` and a colored edge, and a status line at the bottom
shows how many unsaved changes you have. This makes accidental moves harmless:

- Press **`u`** to undo the last move one step at a time.
- Press **`c`** to discard every staged move and return to the saved state.
- Press **`s`** to commit all staged moves at once. Only then are the authoritative Markdown
  files (and, in the hybrid backends, the database mirror) updated. Save is conflict-aware: if
  another process moved a task since the board loaded, that staged move is skipped and reported
  rather than overwriting the newer state. Task writes are serialized by an advisory lock so a
  concurrent board save and CLI move on the same machine don't race.

Moves only step between adjacent lifecycle states (forward or backward); moving past
`backlog` or `done` rings the bell. If you press `q` with unsaved changes, the board warns you
and waits — press `s` to save, `c` to discard, or `q` again to quit without saving.

## Task detail

Press `Enter` (or click a card, or press `d`) to open a read-only overlay with the task's full
Markdown body — objective, scope, acceptance criteria, and activity log. Press `Esc` or `q` to
close it and return to the board.

For tasks that `factory orchestrate` has dispatched to an agent, the card shows the assigned
tool and elapsed time, for example `TASK-0002 · Cart service  [codex · 2h]`. This is joined
from `.factory-state/orchestration/active.yaml`, so a glance at the `DOING` column tells you
which agent is on which task and for how long. For tasks worked manually (no orchestration
record), the card instead shows the task's `Owner` metadata value as `@owner` when it is set.

## Relationship To `factory task move`

The board is a visual front end for the same operation as `factory task move <id> <state>`.
Either path enforces the same lifecycle and storage backend, so they can be mixed freely.
