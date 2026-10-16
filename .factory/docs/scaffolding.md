# Source Scaffolding

Source scaffolding is a separate, owner-controlled phase after project initialization. `factory init` still creates specifications, decisions, instructions, and workflow artifacts only. It never runs framework generators or installs application dependencies.

## Flow

```text
Approved stack decisions
        ↓
factory scaffold plan
        ↓
adapter availability + command preview
        ↓
factory scaffold apply
        ↓
isolated temporary staging
        ↓
validation + create/keep/conflict/invalid plan
        ↓
owner conflict review
        ↓
atomic project publish + generated.yaml
        ↓
optional dependency review and install
```

Only technology choices marked `Approved` are eligible. `Preferred`, `Proposed`, and `Unknown` choices remain specification inputs and cannot trigger source generation.

## Commands

```text
factory scaffold plan -C <project-dir>
factory scaffold apply -C <project-dir>
factory scaffold apply -C <project-dir> --with-deps --allow-network
factory scaffold apply -C <project-dir> --skip-deps
factory scaffold validate -C <project-dir>
```

`plan` is read-only. It resolves each approved technology to exactly one adapter and reports the command, adapter version, expected paths, executable availability, unsupported targets, and ambiguous matches.

`apply` recreates the plan, runs every adapter below a fresh temporary directory, validates the staged output, and displays the complete publish plan. A terminal run uses a Textual Markdown review with a conflict editor. A non-interactive run publishes only new or identical files and leaves every conflict unresolved.

After a successful interactive publish, Factory previews project dependency commands and asks whether to install them. `--with-deps` enables the same phase for non-interactive runs and `--allow-network` grants its required network boundary. `--skip-deps` stops after source publication. Scaffold and dependency execution are separate transactions: a package-manager failure cannot roll back valid source and is retried with `factory deps apply`.

`validate` checks scaffold metadata, approved-stack provenance, managed file hashes, and executable bits. The top-level `factory validate` includes the same checks.

The scaffold foundation does not silently fall back to AI when no adapter supports an approved choice. `plan` reports unsupported source stacks and writes nothing.

## Built-in Providers

| Approved choice | Provider | Published root | Dependency preparation |
| --- | --- | --- | --- |
| React + TypeScript | Vite `react-ts` | `frontend/` | Install deferred |
| Vue + TypeScript | Vite `vue-ts` | `frontend/` | Install deferred |
| Angular + TypeScript | Angular CLI | `frontend/` | Generator uses `--skip-install` |
| Next.js | `create-next-app` | `frontend/` | Generator uses `--skip-install` |
| SvelteKit | Svelte `sv create` | `frontend/` | Generator uses `--no-install` |
| Python + Django | `django-admin startproject` | `backend/` | Adds a project `pyproject.toml` |
| Python + FastAPI + REST | Factory-maintained deterministic baseline | `backend/` | Adds a project `pyproject.toml` |
| Python CLI | Factory-maintained deterministic baseline | `backend/` | Adds a project `pyproject.toml` |
| Node.js + NestJS | Nest CLI | `backend/` | Generator uses `--skip-install` |
| Java + Spring Boot | Spring CLI and Initializr | `backend/` | Maven wrapper generated without resolving dependencies |
| ASP.NET Core Web API | .NET SDK template | `backend/` | Template uses `--no-restore` |
| Go + Gin REST | Factory-maintained deterministic baseline | `backend/` | Pinned module declared without downloading dependencies |
| Flutter | `flutter create` | `mobile/` | Generator uses `--no-pub` |

The invocations follow the official [Vite](https://vite.dev/guide/), [Angular CLI](https://angular.dev/cli/new), [Next.js](https://nextjs.org/docs/pages/api-reference/cli/create-next-app), [Svelte CLI](https://github.com/sveltejs/cli), [Django](https://docs.djangoproject.com/en/6.0/ref/django-admin/), [NestJS](https://docs.nestjs.com/cli/usages), [Spring Boot CLI](https://docs.spring.io/spring-boot/cli/using-the-cli.html), [.NET templates](https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-new), and [Flutter](https://docs.flutter.dev/reference/flutter-cli) command contracts. The Go baseline follows the official [Go REST tutorial with Gin](https://go.dev/doc/tutorial/web-service-gin) and pins its Gin module version for reproducibility.

Node-based adapters require `npm` or `npx` and may need network access to download the generator into the package-manager cache. Django uses `django-admin` from `PATH` or falls back to `python -m django` when Django is installed in Factory's current virtual environment; Factory never bypasses an externally managed Python installation. Flutter requires the SDK's `flutter` executable. Missing tools make the read-only plan unavailable and include an actionable setup hint.

Only `frontend`, `mobile`, and `backend` choices require a source provider. Approved database, infrastructure, CI/CD, deployment, and testing choices are retained as hashed context decisions and shown as warnings; they are not falsely treated as standalone project generators. After the source baseline exists, `factory stack plan|apply|validate` can derive the explicitly supported database and CI configuration described in `stack-configuration.md`.

## Adapter Contract

A scaffold adapter owns one or more technology targets and implements four operations:

- `supports(target)` identifies exact technology choices the adapter owns.
- `preview(targets)` detects its executable and returns its version, command, expected paths, and availability without writing.
- `execute(targets, staging_dir)` writes only below the supplied staging directory.
- `validate(targets, staging_dir)` returns blocking findings for generated output.

Adapters may wrap official technology CLIs or render explicit Factory-maintained deterministic templates when the technology has no project CLI. They must not write directly to the project, install global or project dependencies, mutate user configuration, or read credentials from Factory state. The Factory CLI is the only publisher.

Each adapter has a stable ID and integer contract version. A changed or missing adapter between planning and staging stops publication.

## Safety And Conflict Rules

- The approved stack is hashed before planning and checked again before staging and publication.
- `.git/`, `.factory/`, `.factory-state/`, root instructions, and canonical project artifacts are reserved paths.
- Symlinks and special files from generators are rejected.
- Two adapters cannot produce the same path.
- Existing matching files are kept; missing files are created.
- Existing differing files are never overwritten automatically.
- Proposed conflict content is saved under `.factory-state/scaffolding/proposals/`.
- Skipped conflicts create `.factory-state/scaffolding/INCOMPLETE` and make validation fail.
- An explicit owner-reviewed conflict resolution may publish edited text or reviewed binary output.
- Source writes are transactional: a publish failure restores overwritten files and removes files created by the failed transaction.

Successful publication records `.factory-state/scaffolding/generated.yaml` with the approved-stack hash, adapter IDs and versions, output hashes, executable flags, and whether each file was generated or owner-reviewed.

## What This Does Not Do

Scaffolding creates the initial project structure selected by an approved provider adapter. Its optional follow-up may install dependencies already declared by that structure, but it does not invent application dependencies. It does not implement features, invent architecture decisions, approve stack choices, configure credentials, merge conflicts automatically, or make generated code production-ready. Normal task, review, and QA workflows begin after the baseline is published and validated.
