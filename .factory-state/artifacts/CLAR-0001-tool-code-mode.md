---
schema_version: 1
id: CLAR-0001
task_id: REQ-0039
status: open
source_artifacts:
  - .factory-state/artifacts/REQ-0039-tool-code-mode.md
  - .factory-state/artifacts/REQ-0009-sandboxed-imports.md
created: 2026-10-19
updated: 2026-10-19
answered_at: null
questions:
  - id: who-can-write
    type: single_choice
    prompt: Who may add or change a Code node?
    required: true
    context: Code runs in the sandbox, but it can still use CPU and time, and anyone with run access can trigger it. The rule is checked on save, import and template use.
    recommendation: permission
    options:
      - value: admin
        label: Admins only
      - value: permission
        label: A new code.write permission, given to admins by default and grantable by role
      - value: editor
        label: Every editor (anyone who may edit the workflow)
    depends_on: null
  - id: network
    type: single_choice
    prompt: May code in the container reach the network?
    required: true
    context: Container traffic does not pass the SSRF guard (core/net.py), so with network on, code can reach internal hosts the server can reach.
    recommendation: blocked
    options:
      - value: blocked
        label: Always off (--network none)
      - value: per-node
        label: Off by default, with a per-node switch (admin flag required)
      - value: open
        label: Always on (bridge)
    depends_on: null
  - id: packages
    type: single_choice
    prompt: Which Python packages are available to the code?
    required: true
    context: Per-node installs need network at run time and add start-up time on each call; a fixed image is built once.
    recommendation: fixed-image
    options:
      - value: stdlib
        label: Standard library only
      - value: fixed-image
        label: A fixed image with chosen packages, set by STUDIO_CODE_IMAGE
      - value: per-node
        label: Per-node requirements installed at run time
    depends_on: null
  - id: credentials
    type: single_choice
    prompt: May code receive stored credentials?
    required: true
    context: Passing a credential lets code call external APIs itself, but it also gives the code author the secret value.
    recommendation: none
    options:
      - value: none
        label: No credentials in the first version
      - value: selected
        label: Credentials picked on the node, passed as env vars
    depends_on: null
  - id: no-docker
    type: single_choice
    prompt: What happens on a server without Docker?
    required: true
    context: The repo import already has a subprocess fallback (STUDIO_IMPORT_RUNTIME=subprocess) with a documented risk.
    recommendation: disabled
    options:
      - value: disabled
        label: Code mode is unavailable; Code nodes fail validation
      - value: subprocess-flag
        label: Allow a host subprocess behind an explicit flag (less safe)
    depends_on: null
answers: {}
---
# Clarification: REQ-0039 Tool node Code mode

Owner decisions for `.factory-state/artifacts/REQ-0039-tool-code-mode.md`. Answer with:

```text
factory clarify CLAR-0001 -C <project-dir>
```

The implementing agent copies the answers into REQ-0039 (Open Questions and Business Rules) before `plan-tasks`.
