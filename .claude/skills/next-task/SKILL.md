---
name: next-task
description: Inspect AI Software Factory project state and identify or prepare the next task based on lifecycle, dependencies, roadmap order, owner gates, and merged delivery state. Use when the user asks what work should be done next.
---

# Next Task

1. Read `.factory/AGENTS.md`, `vision.md`, `project.md`, and `roadmap.md`.
2. Inspect `.factory-state/tasks/` by lifecycle without scanning unrelated artifacts.
3. Resolve lifecycle inconsistencies first, such as a merged PR whose task still sits in QA or review.
4. Prefer an active `doing`, `review`, or `qa` task over starting backlog work.
5. For backlog selection, follow explicit dependencies, screen sequence, owner review gates, priority, and recent decisions. Do not choose only by task number.
6. Check Git and PR state when it changes whether a dependency is complete.
7. State the recommended next task and the reason concisely.

Do not create a branch, move a task, or start implementation. When the user confirms which task to start, hand off to `task-start`.
