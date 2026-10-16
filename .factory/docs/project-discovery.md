# Project Discovery

Project repositories own their technology stack, domain, architecture, and delivery choices. The factory framework only defines how agents discover and record those choices.

## Discovery Rules

- Inspect repository files before selecting commands, tools, standards, or implementation patterns.
- Treat stack evidence as observed facts only when supported by files such as manifests, lockfiles, source layout, configuration, tests, docs, CI, containers, or deployment files.
- Do not introduce a language, framework, package manager, database, hosting platform, or architecture pattern unless the project artifacts require it or an approval record exists.
- Record uncertain findings as assumptions or open questions instead of acting on them as facts.
- Update project artifacts when discovery changes how work should be planned, implemented, reviewed, tested, or delivered.

## Technology Evidence Examples

The examples below are evidence sources, not factory-level preferences.

- JavaScript or TypeScript may be evidenced by `package.json`, lockfiles, `tsconfig.json`, source extensions, or tool configuration.
- Python may be evidenced by `pyproject.toml`, `requirements.txt`, lockfiles, source layout, or test configuration.
- Go may be evidenced by `go.mod`, `go.sum`, or Go source layout.
- Java or Kotlin may be evidenced by `pom.xml`, `build.gradle`, Gradle wrappers, or source layout.
- Rust may be evidenced by `Cargo.toml` and `Cargo.lock`.
- Containers or deployment may be evidenced by `Dockerfile`, compose files, Kubernetes manifests, infrastructure code, CI workflows, or runbooks.

## Required Discovery Outputs

Record discovery in `project.md`, `.factory-state/standards/`, `.factory-state/decisions/`, or `.factory-state/artifacts/` using `templates/discovery-template.md`.

At minimum, discover or explicitly mark unknown:

- Install command.
- Development or run command.
- Test command.
- Build command.
- Lint command.
- Typecheck command.
- Format command.
- Migration or database command, when applicable.
- Runtime and deployment notes, when applicable.
- Project-specific coding, testing, review, documentation, security, delivery, and operations conventions.

## First Project Task

New project repositories should start with an onboarding task that discovers project context and records the findings before implementation work begins.

## Project Specs Onboarding

If a project starts with `project-specs.md`, treat it as the source specification for onboarding. Convert it into factory artifacts instead of relying on the original document as private context.

Use `templates/project-specs-template.md` when creating a new `project-specs.md` from scratch.

Use the `onboard-specs` skill, or `templates/prompts/onboard-project-specs.md`,
to guide the conversion. Then run `factory ready` before implementation.

The conversion should update or create:

- `vision.md` for vision, problem, goals, and non-goals.
- `project.md` for domain, actors, modules, constraints, assumptions, and discovered or declared stack.
- `roadmap.md` for MVP, milestones, phases, and priorities.
- Requirement artifacts in `.factory-state/artifacts/` for features, user stories, rules, and acceptance criteria.
- Design artifacts in `.factory-state/artifacts/` for UI, UX, screens, flows, states, content, accessibility, or responsive behavior.
- Architecture artifacts in `.factory-state/artifacts/` or decision records in `.factory-state/decisions/` for stack, integrations, data, deployment, and major technical constraints.
- Task artifacts in `.factory-state/tasks/backlog/` or `.factory-state/tasks/todo/` for roadmap implementation units.

When `project-specs.md` declares a stack before source files exist, record the stack and commands as declared, expected, or proposed according to the wording in the spec. Do not describe them as observed until repository files provide evidence.
