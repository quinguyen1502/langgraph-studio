# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0058
- Status: todo
- Phase: release
- Owner: Thái Quí Nguyễn
- Created: 2026-10-19
- Updated: 2026-10-19
- Requirement IDs: none (a product rename, no feature change)
- Design IDs: none
- Architecture IDs: DEC-0009, DEC-0008

## Objective

Rename the product from "LangGraph Studio" to **Superstep** everywhere a user, operator or contributor sees the name,
without breaking existing installs: stored secrets, signed links, Compose volumes, exported templates and copied nodes
keep working. "LangGraph" stays only where it describes the engine ("built on LangGraph").

## Why

LANGGRAPH is a trademark filed by LangChain Inc. (USPTO serial 98546188, 2024-05-12), and LangChain shipped its own
"LangGraph Studio" (now LangSmith Studio). The shared name confuses search results and carries trademark risk.
"Superstep" is the execution unit of the engine (Pregel / LangGraph supersteps); on 2026-10-19 the name was free on
PyPI and npm and no software product used it.

## Scope

Measured on `origin/develop` (eb4c2f3): "LangGraph Studio" in 50 files, `langgraph-studio` in 255 files, of which 214
are history under `.factory-state/` (left as is).

### In Scope

1. **UI** (`frontend/`)
   - `index.html` title; the brand text in `editor-header.tsx`, `pages/Workflows.tsx`, `pages/settings/SettingsPage.tsx`.
   - Locales en + vi, identical keys: `loginTitle`, `titlePh`, `errors.APPROVAL_IDENTITY_UNKNOWN`.
   - `lib/templates.ts` `TEMPLATE_FORMAT` and `lib/clipboard.ts` `CLIP_FORMAT` become `superstep/template` and
     `superstep/nodes`; reading still accepts the old `langgraph-studio/*` values. `CLIP_KEY` (`lgs.clipboard`) and other
     `lgs.*` localStorage keys stay, so open sessions keep their state.
2. **Backend** (`backend/`)
   - User-facing strings: e-mail subjects and bodies (`auth_service`, `notification_service`, `approval_channels/links`),
     chat messages en + vi (`approval_channels/messages.py`, `base.py` `open_label`), the FastAPI title in `main.py`.
   - `core/errors.py` `CATALOG` message of `APPROVAL_IDENTITY_UNKNOWN`, with `docs/api-errors.md` and both locales.
   - `engine/templates.py` `FORMAT` becomes `superstep/template`; import also accepts `langgraph-studio/template`.
   - `engine/mcp_client.py` client name; `services/telemetry.py` default service, tracer and meter names; the
     `OTEL_SERVICE_NAME` default in `.env.example` and `docker-compose.yml`.
   - Default data directory `~/.superstep/` (`secret.key`, `imports/`). When `~/.superstep/secret.key` is missing and
     `~/.langgraph-studio/secret.key` exists, use the old file, so stored credentials still decrypt.
   - `pyproject.toml`: `name = "superstep-backend"`, description.
   - Tests that assert the old strings (`test_approval_channels`, `test_local_providers`, `test_templates`), plus new
     tests: old template format imports, old key path is picked up.
3. **Compose**: `name: superstep`, with the three volumes pinned to their current names
   (`langgraph-studio_pgdata`, `_redisdata`, `_apidata`) so an existing stack keeps its database (see open question 2).
4. **Handbook** (`handbook/`, en + vi)
   - `site_name`, copyright, `repo_url`, `repo_name`, `site_url`, `extra.alternate` links, `check_images.py` prefix.
   - Every page that names the product or the repo URL (home, start, install, editor, templates, accounts, providers,
     import, configuration, errors, FAQ); the FAQ entry on LangChain's Studio is rewritten for the new name.
   - `README.md` of the handbook, `extra.css` header comment.
   - Screenshots retaken with `HANDBOOK_SHOTS` (the brand shows in the header and on the login page).
5. **Video** (`scripts/promo/`): title, opening and closing words, the `git clone` line and the URL in `video.html`;
   rerun `quickstart.spec.ts` for frames and re-render en + vi (mp4 and poster).
6. **README.md / README.vi.md**: title, definition, badges, every documentation link, clone commands.
7. **Project docs**: `vision.md`, `project.md` (project name), `roadmap.md` (a TASK-0058 line). Old PR links keep
   working through GitHub's redirect and are not rewritten. `project-specs.md` is source context and stays as is.
8. **Redirect for the old docs URL** (`scripts/pages-redirect/`): a `langgraph-studio/` folder with `index.html` and
   `404.html` that send any `/langgraph-studio/<path>#<hash>` to the same page under `/superstep/` (meta refresh, a
   script that keeps the path and hash, `rel=canonical`, a visible link), and a short README on how to publish it.
   It is published from the owner's **user site** repo `quinguyen1502.github.io` (folder `langgraph-studio/`), not from
   a new repo named `langgraph-studio`: GitHub drops the redirect of a renamed repo once a new repo takes the old name,
   which would break old clone URLs and PR links. On 2026-10-19 the user site repo did not exist yet.

### Out Of Scope (owner actions or later tasks)

- **Renaming the GitHub repository** to `superstep` (Settings → General): a repository setting, done by the owner after
  this task merges. GitHub redirects git and web URLs, but **not GitHub Pages**: `quinguyen1502.github.io/langgraph-studio/`
  stops working, and the docs move to `quinguyen1502.github.io/superstep/`. The PR is written for the new URLs, so it is
  merged only right before the rename.
- **Creating the user site repo** `quinguyen1502.github.io` and turning on its Pages: owner action, after the rename;
  this task supplies the files (scope item 8).
- Python package `app`, the `STUDIO_*` environment variables, the `studio-code:1` image, database names: internal or
  operator-facing configuration; renaming them would break deployments for no user gain.
- The HMAC derivation prefix in `core/crypto.py` (`b"langgraph-studio:"`): changing it invalidates every pending approval
  link, identity code and Slack OAuth state. It stays, with a comment saying why.
- Rewriting `.factory-state/` history, the v0.1.0 release notes and the tag.
- The local working folder name.

## Inputs

- Owner decision on 2026-10-19: name **Superstep**.
- Name checks on 2026-10-19: PyPI 404, npm 404, 48 GitHub repos named like it (largest ★16, unrelated), no software
  product in a web search.

## Related Artifacts

- Requirements: none
- Design: none
- Architecture: `docs/backend-architecture.md` (DEC-0009), `docs/ui-conventions.md` (DEC-0008)
- Decisions: owner answers of 2026-10-19 in "Owner Decisions" below
- Discovery: this task's Scope section
- Clarifications: none

## Expected Outputs

- One PR to `develop` with the changes above, new handbook images and video, green CI.
- After merge and a release to `main`: the owner renames the repo; the handbook deploys to the new Pages URL; the
  owner creates `quinguyen1502.github.io` with the redirect folder; a `v0.2.0` release notes the rename and the
  compatibility kept.

## Constraints

- shadcn and theme tokens only; en/vi locale keys identical; new strings in both locales.
- Error catalog change in `CATALOG`, `docs/api-errors.md` and both locales together (`test_api_envelope.py`).
- No schema change, no migration.

## Dependencies

- None in code. The repo rename (owner) follows the merge.

## Acceptance Criteria

- `git grep -n "LangGraph Studio"` outside `.factory-state/` returns only the FAQ sentence that names LangChain's former
  product.
- `git grep -n "langgraph-studio"` outside `.factory-state/` returns only the compatibility points: old template and
  clipboard formats accepted, the old key path fallback, the HMAC prefix, the pinned Compose volume names, the redirect
  files in `scripts/pages-redirect/`, and PR links in `roadmap.md`.
- An exported template from v0.1.0 (`langgraph-studio/template`) imports; a new export says `superstep/template`.
- With only `~/.langgraph-studio/secret.key` present, existing credentials decrypt and a pending approval link from
  before the change still works.
- `docker compose up` on a stack started with v0.1.0 keeps its workflows and runs.
- Handbook builds strict for en and vi; `check_images.py` passes; the video shows "Superstep" and the new URL.
- Opened locally, `scripts/pages-redirect/langgraph-studio/404.html` at `/langgraph-studio/run/schedules/#x` lands on
  `/superstep/run/schedules/#x`; `/langgraph-studio/vi/` lands on `/superstep/vi/`.
- Backend pytest (Python 3.12), frontend build, test, lint and e2e pass.

## Validation

- Python 3.12 venv: full pytest suite.
- `frontend/`: `npm run build`, `npm test`, `npm run lint`, Playwright e2e.
- `zensical build` for both configs, `python check_images.py site`.
- Compose upgrade check: start v0.1.0, create a workflow, switch to this branch, `docker compose up --build`, the
  workflow is still there.

## Owner Decisions

Answered by the owner on 2026-10-19; the proposals were accepted as written.

1. **Product name in the UI**: "Superstep" everywhere, no "Studio" suffix.
2. **Compose**: `name: superstep`, the three volumes pinned to their v0.1.0 names, so existing stacks keep their data.
3. **Tagline**: the current definition with only the name changed; "LangGraph" stays as the engine it builds on.
4. **Old Pages URL**: redirected, not left to 404. The redirect files are part of this task (scope item 8); they are
   served from the user site repo rather than a new `langgraph-studio` repo, for the reason given there.

## Open Questions

- None.
