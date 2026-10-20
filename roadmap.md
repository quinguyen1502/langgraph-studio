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

## Delivery records

- TASK-0033 Align requirement status and the integration branch (REQ-0021, Implemented 2026-10-18): **done** — PR [#36](https://github.com/quinguyen1502/langgraph-studio/pull/36). DEC-0033 supersedes DEC-0002. REV-0032, QA-0032.
- TASK-0034 JSON fold tooltip and `spliceNode` tests (REQ-0022, Implemented 2026-10-18): **done** — PR [#37](https://github.com/quinguyen1502/langgraph-studio/pull/37). REV-0033, QA-0033.

## Node input

- TASK-0035 Per-node input fields (REQ-0023, Implemented 2026-10-18): **done** — PR [#38](https://github.com/quinguyen1502/langgraph-studio/pull/38). REV-0034, QA-0034.

## Run one step

- TASK-0036 Run one superstep, or until a chosen node, then pause (REQ-0024, Approved 2026-10-18): **done** — PR [#39](https://github.com/quinguyen1502/langgraph-studio/pull/39) merged into `develop` 2026-10-18. REV-0035, QA-0035. Independent of TASK-0037.

## Canvas note

- TASK-0037 Sticky note on the flowchart (REQ-0025, Approved 2026-10-18): **done** — PR [#40](https://github.com/quinguyen1502/langgraph-studio/pull/40) merged into `develop` 2026-10-18. REV-0036, QA-0036. Independent of TASK-0036.

## Editor panels

- TASK-0038 Drag to resize the palette, the config panel, and the run panel (REQ-0026, Implemented 2026-10-18): **done** — PR [#41](https://github.com/quinguyen1502/langgraph-studio/pull/41) merged into `develop` 2026-10-18. REV-0037, QA-0037.

## Review hardening

- TASK-0039 Fixes from the 2026-10-18 project review: HTTP Tool SSRF guard, Condition matching, macOS Playwright, editor header at 1280px, records, CORS, log redaction, lazy routes (REQ-0027, Implemented 2026-10-18): **done** — PR [#42](https://github.com/quinguyen1502/langgraph-studio/pull/42) merged into `develop` 2026-10-18. REV-0038, QA-0038.

## Editor maintenance

- TASK-0040 Split `Editor.tsx` into `components/editor/` and clear the React hook oxlint warnings (REQ-0028, Implemented 2026-10-18): **done**. REV-0039, QA-0039. Merged (PR #43).
- TASK-0041 Template editor with state field chips for node message fields (REQ-0029, Implemented 2026-10-18), with the editor header overlap and `sm` button icon offset: **done**. REV-0040, QA-0040. Merged (PR #44).
- TASK-0042 Commit `.claude/launch.json` (backend and frontend dev servers for the Claude app preview): **done**. Merged (PR #45).
- TASK-0043 Template insert menu focus and vendor chunks (REQ-0030, Implemented 2026-10-18): **done**. REV-0041, QA-0041. Merged (PR #47).
- TASK-0044 Template paths and filters (REQ-0031, DEC-0034, Implemented 2026-10-18): **done**. REV-0042, QA-0042. Merged (PR #48).

## Sign-in hardening

- TASK-0045 Sign-in lockout, password reset links, HttpOnly session cookie, no demo account in production (REQ-0032, DEC-0035, Implemented 2026-10-18): **done**. REV-0043, QA-0043. Merged (PR #49).

## Scheduled runs

- TASK-0046 Cron schedules for workflow runs (REQ-0033, DEC-0036, Implemented 2026-10-19): **done**. REV-0044, QA-0044. Merged (PR #50).

## More approval channels

- TASK-0047 WhatsApp buttons, e-mail and Teams links to /approve (REQ-0034, DEC-0037, Implemented 2026-10-19): **done**. REV-0045, QA-0045. Merged (PR #51).

## Records

- TASK-0048 Close the open questions of REQ-0001, 0002, 0003, 0004, 0008 and 0010; accept DEC-0006; DEC-0033 addendum on release merges to main: **done**. Merged (PR #52).

## Loops

- TASK-0049 For each node: run a branch once per list item, one at a time (REQ-0035, DEC-0038, Implemented 2026-10-19): **done**. REV-0046, QA-0046. Merged (PR #54).

## Decision models

- TASK-0050 Decision (Jev) node: typed questions to TypeSafe System One, answers to state (REQ-0036, DEC-0039, Implemented 2026-10-19): **done**. REV-0047, QA-0047. Merged (PR #55).

## E-mail

- TASK-0051 SMTP credentials and Send email node: dry run without a credential, effectively-once sending, hourly recipient quota (REQ-0037, DEC-0040, Implemented 2026-10-19): **done**. REV-0048, QA-0048. Merged (PR #56).

## Accounts

- TASK-0052 Profile page and self-service password change (REQ-0038): **merged** (PR #58, REV-0049, QA-0049).

## Code nodes

REQ-0039, Accepted and Implemented 2026-10-19; CLAR-0001 answered; DEC-0041 Accepted 2026-10-19; tasks approved by the owner.

- TASK-0053 Code mode runtime: Docker sandbox with no network, `studio-code` image, node mode and validation. **merged** (PR #61, REV-0050, QA-0050). Independent of TASK-0054.
- TASK-0054 `code.write` permission, checked on every path that writes a graph. **merged** (PR #62, REV-0051, QA-0051). Independent of TASK-0053.
- TASK-0055 Editor: Python code field, Test with sample state, trace output. **merged** (PR #63, REV-0052, QA-0052). After TASK-0053 and TASK-0054.
- TASK-0056 Host subprocess runtime and the eight "not isolated" warnings. **merged** (PR #64, REV-0053, QA-0053). After TASK-0053 and TASK-0055.

## Documentation

- Handbook on Zensical (English and Vietnamese sites from one page tree), a platform-style README, and a 70 s quickstart video recorded from the UI by `frontend/e2e/quickstart.spec.ts` (`handbook/`, `scripts/promo/`): **in review** (PR #65).

## Rename

- TASK-0058 Rename the product to **Superstep** (UI, backend strings, Compose, handbook, video, README), keeping v0.1.0 installs working: **merged** (PR #69, plan PR #68, REV-0054, QA-0054); released to `main` in PR #70. The owner renamed the repository on 2026-10-20 and chose not to redirect the old docs URL, so the redirect files were removed.
- TASK-0059 Never drop the history write of a cancelled run (flaky Postgres CI: `test_disconnect_cancels_run`, `test_timeout`, approval callback): **merged** (PR #73, REV-0055, QA-0055). The Postgres CI job passed 4 consecutive runs before the merge.
- TASK-0060 Clear the run bus entry of a run cancelled while the loop shuts down (REV-0055 follow-up): **merged** (PR #76, REV-0056, QA-0056).
- TASK-0061 Center the search icon and clear button in search boxes (owner report): **merged** (PR #77).
- TASK-0062 Docs tell readers to sign up instead of using the demo account (owner request): **merged** (PR #80).

## Channel templates and logos

REQ-0040, Accepted 2026-10-20 (the owner chose brand colours and 8 templates).

- TASK-0063 Channel logos in brand colours (Channels, My accounts, Human node select, Audit log, connection items), DEC-0042: **merged** (PR #83, REV-0057, QA-0057).
- TASK-0064 Eight built-in templates (five channel approvals, two-level approval, support escalation, batch), built-in names in en and vi, logos on gallery cards: **todo**, after TASK-0063.
