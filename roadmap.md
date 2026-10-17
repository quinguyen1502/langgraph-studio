# Roadmap

Phases accepted by the owner on 2026-10-16 (DEC-0007, supersedes the P0/P1/P2 bands of DEC-0004). Task IDs follow phase order; old IDs are mapped in `docs/factory-task-renumbering.md`.

## MVP baseline (done)

- REQ-0001 MVP baseline — implemented and verified (see DISC-0001)

## Phase 1 — Feasibility (login, workflow list, simple core)

Status as of 2026-10-16 (nothing merged yet; all PRs are drafts).

| # | Task | Title | Status | PR | Branch base |
|---|---|---|---|---|---|
| 1 | TASK-0001 | Confirm project context and technical baseline | review | (on `main`) | — |
| 2 | TASK-0002 | CI + Factory deps/verify unblock | review | [#1](https://github.com/quinguyen1502/langgraph-studio/pull/1) | `main` |
| 3 | TASK-0003 | Harden auth/login and workflow list | review | [#5](https://github.com/quinguyen1502/langgraph-studio/pull/5) | #4 branch (+ merges #1) |
| 4 | TASK-0004 | Review and harden core MVP compiler, runtime and run API | review | [#7](https://github.com/quinguyen1502/langgraph-studio/pull/7) (plan: [#3](https://github.com/quinguyen1502/langgraph-studio/pull/3)) | #6 branch |
| 5 | TASK-0005 | Real LLM providers with per-workflow credentials | review | [#9](https://github.com/quinguyen1502/langgraph-studio/pull/9) (replaces [#2](https://github.com/quinguyen1502/langgraph-studio/pull/2)) | #8 branch |
| 6 | TASK-0016 | Run trace timeline UI | review | [#6](https://github.com/quinguyen1502/langgraph-studio/pull/6) | #5 branch |
| 7 | TASK-0017 | Restructure backend into layers (SQLAlchemy + Alembic) | review | [#8](https://github.com/quinguyen1502/langgraph-studio/pull/8) | #7 branch |
| 8 | TASK-0018 | API envelope, English error codes, frontend i18n (en/vi) | review | [#10](https://github.com/quinguyen1502/langgraph-studio/pull/10) | #9 branch |
| — | (re-plan) | Phases + task renumbering (DEC-0007) | — | [#4](https://github.com/quinguyen1502/langgraph-studio/pull/4) | `main` |

**Merge order:** #4 → #1 → #3 → #5 → #6 → #7 → #8 (TASK-0017) → #9 (TASK-0005) → #10 (TASK-0018). PR #2 is superseded by #9 (same feature on the layered backend) and can be closed without merging. After each merge, retarget the next stacked PR to `main`. PR #3 (TASK-0004 plan only) is superseded by #7 and can be closed once #7 merges, or merged first; its files are identical on #7.

## Phase 2 — Usable

Status for all Phase 2–4 tasks: backlog.

- TASK-0006 Human-in-the-loop (REQ-0003): **in review** (draft PR into `develop`, stacked on TASK-0010)
- TASK-0007 API / webhook trigger (REQ-0004): **in review** (draft PR into `develop`, stacked on TASK-0006)
- TASK-0008 Workflow versioning (REQ-0005): **in review** (draft PR into `develop`, stacked on TASK-0007)
- TASK-0009 Postgres + Redis + Docker Compose (REQ-0008): **in review** (draft PR into `develop`)
- TASK-0010 Observability (REQ-0010): **in review** (draft PR into `develop`, stacked on TASK-0009)
- TASK-0019 Phase-2 hardening (open issues of TASK-0006/7/8/9/10): **in review** (draft PR into `develop`, stacked on TASK-0008)
- TASK-0020 Deferred hardening (notifications, webhook delivery log/retry/rotation, checkpoint recovery, lease reaper, live spans + OTel metrics): **in review** (draft PR into `develop`, stacked on TASK-0019)
- TASK-0021 Effectively-once side effects (idempotency keys, node ledger, fencing), fan-out/imported checkpoints, lost-span export, live notifications + preferences: **in review** (draft PR into `develop`, stacked on TASK-0020)
- TASK-0022 Human-in-the-loop approval through external channels (Slack, Telegram; adapter interface for WhatsApp/Teams/e-mail later): **in review** (draft PR into `develop`, stacked on TASK-0021). Follow-up commits on the same PR: verified identities (one-time code by bot DM), org-wide admin channels, en/vi chat texts, API `callback_url` after a channel resume, several Slack workspaces per owner (team_id routing), callback rate limits

## Phase 3 — Advanced

- TASK-0011 Subgraphs and parallel branches (REQ-0006)
- TASK-0012 RAG node (REQ-0007)
- TASK-0013 MCP tools (REQ-0011)
- TASK-0014 RBAC and sharing (REQ-0012)

## Phase 4 — Last

- TASK-0015 Repo import hardening + container sandbox (REQ-0009). The existing import feature is **experimental**; TASK-0015 puts it behind `STUDIO_ENABLE_IMPORT` (default off in UI and API). Not changed yet.
