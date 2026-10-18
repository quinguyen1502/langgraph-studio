# Roadmap

Phases accepted by the owner on 2026-10-16 (DEC-0007, supersedes the P0/P1/P2 bands of DEC-0004). Task IDs follow phase order; old IDs are mapped in `docs/factory-task-renumbering.md`.

## MVP baseline (done)

- REQ-0001 MVP baseline — implemented and verified (see DISC-0001)

## Phase 1 — Feasibility (login, workflow list, simple core)

Status as of 2026-10-17: all Phase 1 work is in `develop` (it was the base of the merged stack #11–#25). The original PRs #1 and #4–#10 still target `main`/stacked branches and stay open, because `main` is not touched.

| # | Task | Title | Status | PR | Branch base |
|---|---|---|---|---|---|
| 1 | TASK-0001 | Confirm project context and technical baseline | done (in `develop`) | (on `main`) | — |
| 2 | TASK-0002 | CI + Factory deps/verify unblock | done (in `develop`) | [#1](https://github.com/quinguyen1502/langgraph-studio/pull/1) | `main` |
| 3 | TASK-0003 | Harden auth/login and workflow list | done (in `develop`) | [#5](https://github.com/quinguyen1502/langgraph-studio/pull/5) | #4 branch (+ merges #1) |
| 4 | TASK-0004 | Review and harden core MVP compiler, runtime and run API | done (in `develop`) | [#7](https://github.com/quinguyen1502/langgraph-studio/pull/7) (plan: [#3](https://github.com/quinguyen1502/langgraph-studio/pull/3)) | #6 branch |
| 5 | TASK-0005 | Real LLM providers with per-workflow credentials | done (in `develop`) | [#9](https://github.com/quinguyen1502/langgraph-studio/pull/9) (replaces [#2](https://github.com/quinguyen1502/langgraph-studio/pull/2)) | #8 branch |
| 6 | TASK-0016 | Run trace timeline UI | done (in `develop`) | [#6](https://github.com/quinguyen1502/langgraph-studio/pull/6) | #5 branch |
| 7 | TASK-0017 | Restructure backend into layers (SQLAlchemy + Alembic) | done (in `develop`) | [#8](https://github.com/quinguyen1502/langgraph-studio/pull/8) | #7 branch |
| 8 | TASK-0018 | API envelope, English error codes, frontend i18n (en/vi) | done (in `develop`) | [#10](https://github.com/quinguyen1502/langgraph-studio/pull/10) | #9 branch |
| — | (re-plan) | Phases + task renumbering (DEC-0007) | — | [#4](https://github.com/quinguyen1502/langgraph-studio/pull/4) | `main` |

**Merge order:** #4 → #1 → #3 → #5 → #6 → #7 → #8 (TASK-0017) → #9 (TASK-0005) → #10 (TASK-0018). PR #2 is superseded by #9 (same feature on the layered backend) and can be closed without merging. After each merge, retarget the next stacked PR to `main`. PR #3 (TASK-0004 plan only) is superseded by #7 and can be closed once #7 merges, or merged first; its files are identical on #7.

## Phase 2 — Usable

Phase 2, Phase 3, and Phase 4 are done and merged into `develop`.

- TASK-0006 Human-in-the-loop (REQ-0003): **done** — merged into `develop` 2026-10-17
- TASK-0007 API / webhook trigger (REQ-0004): **done** — merged into `develop` 2026-10-17
- TASK-0008 Workflow versioning (REQ-0005): **done** — merged into `develop` 2026-10-17
- TASK-0009 Postgres + Redis + Docker Compose (REQ-0008): **done** — merged into `develop` 2026-10-17
- TASK-0010 Observability (REQ-0010): **done** — merged into `develop` 2026-10-17
- TASK-0019 Phase-2 hardening (open issues of TASK-0006/7/8/9/10): **done** — merged into `develop` 2026-10-17
- TASK-0020 Deferred hardening (notifications, webhook delivery log/retry/rotation, checkpoint recovery, lease reaper, live spans + OTel metrics): **done** — merged into `develop` 2026-10-17
- TASK-0021 Effectively-once side effects (idempotency keys, node ledger, fencing), fan-out/imported checkpoints, lost-span export, live notifications + preferences: **done** — merged into `develop` 2026-10-17
- TASK-0022 Human-in-the-loop approval through external channels (Slack, Telegram; adapter interface for WhatsApp/Teams/e-mail later): **done** — merged into `develop` 2026-10-17. Follow-up commits on the same PR: verified identities (one-time code by bot DM), org-wide admin channels, en/vi chat texts, API `callback_url` after a channel resume, several Slack workspaces per owner (team_id routing), callback rate limits; then per-workspace identities, a DB-enforced single verified owner, one idempotent callback path for every resume source, `STUDIO_TRUSTED_PROXIES`, and a Settings page (`/settings/channels|accounts|audit`) replacing the dialog

## Phase 3 — Advanced

- TASK-0011 Subgraphs and parallel branches (REQ-0006): **done** — merged into `develop` 2026-10-17 (PR #21)
- TASK-0012 RAG node (REQ-0007): **done** — merged into `develop` 2026-10-17 (PR #22)
- TASK-0013 MCP tools (REQ-0011): **done** — merged into `develop` 2026-10-17 (PR #23)
- TASK-0014 RBAC and sharing (REQ-0012): **done** — merged into `develop` 2026-10-17 (PR #24)
- TASK-0029 Phase 3 hardening (teams, ownership transfer, audit log, user deletion, org-resource policy, subgraph leftovers; DEC-0024): **done** — merged into `develop` 2026-10-17 (PR #25). Slack Enterprise Grid stays out of scope.

## Phase 4 — Last

- TASK-0015 Repo import hardening + container sandbox (REQ-0009). **done** — merged into `develop` 2026-10-18 (PR #33). The import feature stays **experimental**; `STUDIO_ENABLE_IMPORT` defaults off. Docker sandbox when the flag is on. REQ-0009 is Implemented (owner accepted Docker on 2026-10-18).

## Phase 5 — Editor UX

Added on 2026-10-17 at the owner's request. Status: done (PRs #26–#31 merged into develop on 2026-10-17).

- TASK-0023 Editor hotkeys and shortcut cheatsheet (REQ-0013) — done, DEC-0026
- TASK-0024 Editor undo and redo history (REQ-0014), after TASK-0023 — done, DEC-0027
- TASK-0025 Workflow template library: starter templates, save as template, import/export (REQ-0015) — done, DEC-0028
- TASK-0026 Copy, paste and duplicate nodes (REQ-0016) — done, DEC-0029
- TASK-0027 Auto-layout for the workflow canvas (REQ-0017) — done, DEC-0030
- TASK-0028 Command palette (REQ-0018) — done, DEC-0031


## LLM providers

- TASK-0030 Local and routed LLM providers: Ollama, LM Studio, generic OpenAI-compatible (vLLM / llama.cpp / LocalAI), OpenRouter; provider registry, model list, test connection (DEC-0032, Accepted 2026-10-18): **done** — PR #32 merged into `develop` (migrations 0024_credential_headers, 0025_kb_dims).

## Node execution settings

- TASK-0031 Per-node retry, timeout, and cache (REQ-0019, Implemented 2026-10-18): **done** — PR [#34](https://github.com/quinguyen1502/langgraph-studio/pull/34). REV-0030, QA-0030.

## Editor polish

- TASK-0032 Editor polish and bilingual README (REQ-0020, Implemented 2026-10-18): **done** — PR [#35](https://github.com/quinguyen1502/langgraph-studio/pull/35). REV-0031, QA-0031.
