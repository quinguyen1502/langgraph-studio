---
name: plan-tasks
description: Split an approved requirement into small Factory task artifacts with dependencies, acceptance criteria, and validation. Use when the user asks to plan, break down, or create tasks from a requirement.
---

# Plan Tasks

Turn one requirement (and its linked design or architecture artifacts) into verifiable tasks.

## Steps

1. Read the requirement and every artifact it references. If acceptance criteria are missing, stop and use `create-requirement`.
2. Choose small-task, medium-task, or large-task workflow from `.factory/workflows/` and follow it.
3. Allocate IDs after fetch:

```bash
git fetch --all --prune
factory ids next TASK --all-refs
```

Request one ID per task you will create. Re-run before push.

4. Write each task from `.factory/templates/task-template.md` under `.factory-state/tasks/`.
5. Place a task in `todo/` only when objective, scope, inputs, outputs, dependencies, acceptance criteria, and validation are all present. Otherwise use `backlog/` and list the open questions.
6. Link requirement, design, architecture, decision, and discovery paths on every task.
7. Do not start a branch or implement. After the owner confirms the set, the next skill is `task-start`.

Run `factory ready` when planning should unblock implementation.
