# Onboard Project Specs Prompt

Use this prompt inside a project repository that already contains `project-specs.md` and uses the AI Software Factory framework in `.factory/`. Prefer the `onboard-specs` skill when it is installed. Allocate artifact IDs with `git fetch --all --prune` and `factory ids next <TYPE> --all-refs`. Run `factory ready` when the conversion should unblock implementation.

```text
You are operating inside a project repository that uses the AI Software Factory framework in `.factory/`.

Input source:
- Read `project-specs.md` as the source specification.
- Read `AGENTS.md`.
- Verify `.factory/AGENTS.md` exists and read it.
- If `.factory/AGENTS.md` is missing and `.factory` is configured as a submodule, initialize it with `git submodule update --init .factory`.
- If `.factory/AGENTS.md` remains unavailable, stop and record a blocker instead of continuing from project-local instructions alone.
- Read `.factory/docs/artifact-model.md`.
- Read `.factory/docs/project-discovery.md`.
- Read `.factory/docs/task-lifecycle.md`.
- Read `.factory/templates/`.

Goal:
Convert `project-specs.md` into factory-compatible project artifacts without relying on chat history.

Rules:
- Do not assume facts not present in `project-specs.md` or existing repository files.
- If `project-specs.md` declares a tech stack, record it as a project constraint or proposed/approved stack according to wording.
- If implementation files do not exist yet, mark commands and stack evidence as expected/proposed, not observed.
- Preserve stack neutrality in factory artifacts except where the project spec explicitly constrains the stack.
- Document assumptions, blockers, and open questions in the generated artifacts.
- Create generated workflow state under `.factory-state/`.
- Keep `.factory/` reserved for reusable framework assets.
- Do not implement source code yet.
- Do not delete or overwrite existing project artifacts unless the update is clearly additive and traceable.

Create or update these files:
- `vision.md`
- `project.md`
- `roadmap.md`
- `.factory-state/artifacts/DISC-0001-project-context.md`
- One or more `.factory-state/artifacts/REQ-xxxx-*.md` files for product requirements/features.
- One or more `.factory-state/artifacts/DES-xxxx-*.md` files if the spec includes UI, UX, screens, flows, or user-facing behavior.
- One or more `.factory-state/artifacts/ARCH-xxxx-*.md` or `.factory-state/decisions/DEC-xxxx-*.md` files if the spec includes architecture, stack, integrations, data, deployment, or major technical constraints.
- `.factory-state/tasks/backlog/` or `.factory-state/tasks/todo/` task artifacts for the MVP/roadmap work.

Artifact mapping:
- Vision, problem, goals, non-goals -> `vision.md`.
- Domain, users, actors, modules, constraints, assumptions -> `project.md`.
- MVP, milestones, phases, priorities -> `roadmap.md`.
- Tech stack, commands, evidence, unknowns -> `.factory-state/artifacts/DISC-0001-project-context.md`.
- Features, user stories, business rules, acceptance criteria -> `.factory-state/artifacts/REQ` artifacts.
- Screens, flows, states, content, accessibility, responsive behavior -> `.factory-state/artifacts/DES` artifacts.
- Architecture, data model, integrations, deployment, major technical choices -> `.factory-state/artifacts/ARCH` or `.factory-state/decisions/DEC` artifacts.
- Implementation units -> `.factory-state/tasks/` artifacts.

Task rules:
- Keep tasks small and verifiable.
- Each task must link related requirement/design/architecture/discovery artifacts.
- Put tasks in `todo` only if scope, inputs, outputs, dependencies, acceptance criteria, and validation are clear.
- Put unclear work in `backlog` with open questions.
- Keep the existing `TASK-0001` project-context task updated or complete it if discovery is now represented elsewhere.

Output:
- Make the file changes.
- Then summarize:
  - files created
  - files updated
  - assumptions recorded
  - open questions
  - recommended next task
```
