# Roadmap

Phases accepted by the owner on 2026-10-16 (DEC-0007, supersedes the P0/P1/P2 bands of DEC-0004). Task IDs follow phase order; old IDs are mapped in `docs/factory-task-renumbering.md`.

## MVP baseline (done)

- REQ-0001 MVP baseline — implemented and verified (see DISC-0001)

## Phase 1 — Feasibility (login, workflow list, simple core)

1. TASK-0001 Confirm project context and technical baseline (review)
2. TASK-0002 CI + Factory deps/verify unblock (PR #1)
3. TASK-0003 Harden auth/login and workflow list (REQ-0001)
4. TASK-0004 Review and harden core MVP compiler, runtime and run API (REQ-0001; PR #3)
5. TASK-0005 Real LLM providers with per-workflow credentials (REQ-0002; PR #2)

## Phase 2 — Usable

- TASK-0006 Human-in-the-loop (REQ-0003)
- TASK-0007 API / webhook trigger (REQ-0004)
- TASK-0008 Workflow versioning (REQ-0005)
- TASK-0009 Postgres + Redis + Docker Compose (REQ-0008)
- TASK-0010 Observability (REQ-0010)

## Phase 3 — Advanced

- TASK-0011 Subgraphs and parallel branches (REQ-0006)
- TASK-0012 RAG node (REQ-0007)
- TASK-0013 MCP tools (REQ-0011)
- TASK-0014 RBAC and sharing (REQ-0012)

## Phase 4 — Last

- TASK-0015 Repo import hardening + container sandbox (REQ-0009). The existing import feature is **experimental**; TASK-0015 puts it behind `STUDIO_ENABLE_IMPORT` (default off in UI and API). Not changed yet.
