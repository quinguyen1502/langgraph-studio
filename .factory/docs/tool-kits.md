# AI Tool Kits

Tool kits translate one canonical, project-owned policy into provider-specific configuration. They are optional; canonical instructions remain usable without them.

## Levels

- `instructions`: generates `AGENTS.md`, the Claude bridge, the canonical policy, metadata, and inactive hook scripts. This is the default.
- `guardrails`: activates project-local Codex and Claude Code permission files, protects factory-owned configuration, and runs report-only `factory validate` when an agent stops.
- `automation`: includes guardrails and may run project validation commands only when their policy evidence is `Observed`. Commands recorded by init are `Expected`, so they are not activated.
- `custom`: uses the same safe renderer while allowing the owner to select hooks explicitly.

Cursor and Grok consume canonical `AGENTS.md`. Factory does not invent a native Cursor or Grok permission or hook layer when no stable equivalent is supported. Grok skills are emitted to `.grok/skills/`.

## Canonical And Generated Files

```text
.factory-state/tooling/
├── tool-policy.yaml       # owner-controlled canonical policy
├── generated.yaml         # policy hash, adapter versions, output hashes
├── hooks/
│   ├── pre_tool_guard.py
│   └── stop_validate.py
└── proposals/             # conflicts requiring owner review

.codex/config.toml         # active Codex permission profile
.codex/hooks.json          # active Codex lifecycle hooks
.claude/settings.json      # active Claude Code permissions and hooks
```

The generated policy denies access to common secret files, keeps `.factory/` and `.factory-state/tooling/` read-only to agents, and asks before selected delivery operations. It never generates `danger-full-access`, bypass-permission modes, broad shell allowlists, credentials, global settings, or provider endpoints.

The pre-tool hook rejects obvious destructive writes to factory-owned assets. It is defense in depth, not a complete security boundary; provider sandbox and permission rules remain authoritative. The stop hook reports validation findings and exits successfully so it cannot trap an agent in a stop loop. Automation commands are limited to owner-marked `Observed` test, lint, typecheck, build, and format commands.

## Workflow

```text
factory tools status -C project
factory tools configure -C project
factory tools configure --no-interactive -C project
factory tools plan -C project
factory tools apply -C project
factory tools validate -C project
```

`configure` opens a Textual form for level, providers, hooks, and command evidence, then a Markdown review with the policy diff, file plan, and provider conflicts. Agents and scripts pass `--no-interactive` instead of the TUI. That path loads the current policy (or a default from `factory.yaml` when the file is missing), applies optional `--level`, `--status`, `--tool`, hook flags, and `--command NAME=COMMAND` overlays, then publishes the same way as `apply`. Existing provider files are still preserved as conflicts.

`apply` creates missing files atomically. It never overwrites an existing provider file without an interactive reviewed replacement. Skipped content conflicts are saved under `proposals/`; skipped stale files remain listed in `INCOMPLETE`. Both cases keep validation incomplete until resolved.

Projects attached to Factory before the tooling bundle existed, or that skipped `import --apply`, will not have `tool-policy.yaml`. A later pin bump does not create it. Re-run `factory import --apply --no-interactive` or `factory tools configure --no-interactive` to backfill. This is a project gap, not a framework defect.

`validate` checks the policy schema, metadata, required generated files, output drift, and the requirement that automation commands have `Observed` evidence. The project-wide `factory validate` includes the same checks.

Codex loads project-local configuration only for trusted projects. Non-managed project hooks also require review of their exact hash; after apply, open Codex in the project and use `/hooks` to review and trust them. Changed generated hooks require a new review. Factory does not bypass this provider trust boundary.

Provider behavior follows the official [Codex hooks](https://developers.openai.com/codex/hooks), [Codex permissions](https://developers.openai.com/codex/permissions), [Claude Code hooks](https://code.claude.com/docs/en/hooks), and [Claude Code permissions](https://code.claude.com/docs/en/permissions) documentation.
