# Factory task renumbering (2026-10-16)

Owner re-plan (DEC-0007): tasks renumbered to follow phase order. Commit messages and branch names created before this date keep the **old** IDs.

| New ID | Old ID | Title | Phase | Existing branch / PR |
| --- | --- | --- | --- | --- |
| TASK-0001 | TASK-0001 | Confirm project context and technical baseline | 1 Feasibility | — |
| TASK-0002 | TASK-0002 | GitHub Actions CI + Factory deps/verify unblock | 1 Feasibility | `factory/task-0002-add-github-actions-ci-for-backend-tests-and-frontend-build` (#1) |
| TASK-0003 | — (new) | Harden auth/login and workflow list | 1 Feasibility | — |
| TASK-0004 | TASK-0014 | Review and harden core MVP compiler, runtime and run API | 1 Feasibility | `factory/task-0014-plan-mvp-hardening` (#3) |
| TASK-0005 | TASK-0003 | Real LLM providers with per-workflow credentials | 1 Feasibility | `factory/task-0003-configure-real-llm-providers-with-per-workflow-credentials` (#2) |
| TASK-0006 | TASK-0005 | Human-in-the-loop interrupt and resume | 2 Usable | — |
| TASK-0007 | TASK-0007 | Trigger workflows via REST API and webhooks | 2 Usable | — |
| TASK-0008 | TASK-0006 | Workflow versioning with diff and rollback | 2 Usable | — |
| TASK-0009 | TASK-0008 | Postgres + Redis + Docker Compose | 2 Usable | — |
| TASK-0010 | TASK-0009 | Tracing and observability for runs | 2 Usable | — |
| TASK-0011 | TASK-0010 | Subgraphs and parallel branches | 3 Advanced | — |
| TASK-0012 | TASK-0011 | RAG retriever node | 3 Advanced | — |
| TASK-0013 | TASK-0012 | MCP tools as Tool node source | 3 Advanced | — |
| TASK-0014 | TASK-0013 | RBAC and workflow sharing | 3 Advanced | — |
| TASK-0015 | TASK-0004 | Repo import hardening + container sandbox (import experimental, `STUDIO_ENABLE_IMPORT`) | 4 Last | — |

Artifacts renamed with tasks: `REV-0002-task-0003.md` → `REV-0002-task-0005.md`, `QA-0002-task-0003.md` → `QA-0002-task-0005.md` (on the #2 branch).

Requirements and decisions keep their IDs (REQ-0001…0012, DEC-0001…0007).
