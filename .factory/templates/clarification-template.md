---
schema_version: 1
id: CLAR-0001
task_id: TASK-0001
status: open
source_artifacts: []
created: YYYY-MM-DD
updated: YYYY-MM-DD
answered_at: null
questions:
  - id: delivery-mode
    type: single_choice
    prompt: Which delivery mode should this task use?
    required: true
    context: Explain why this decision is needed.
    recommendation: incremental
    options:
      - value: incremental
        label: Incremental delivery
      - value: single-release
        label: Single release
    depends_on: null
answers: {}
---
# Clarification

Use this artifact when a task has at least four owner questions, a long checklist, multiple groups, or conditional questions. Link it directly from the task artifact.

The owner may answer it with:

```text
factory clarify CLAR-0001 -C <project-dir>
```

The implementing agent must propagate submitted answers into the related requirement, design, architecture, decision, or task artifacts.
