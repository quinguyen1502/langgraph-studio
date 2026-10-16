# Stack Configuration

Stack configurators convert explicit `Approved` technology decisions into deterministic, reviewable repository configuration. This phase follows specification approval and is independent from source scaffolding and dependency installation.

## Flow

```text
factory stack plan -C <project-dir>
factory stack apply -C <project-dir>
factory stack validate -C <project-dir>
```

`plan` reads project intake and `.factory-state/factory.yaml`, hashes all approved choices and the integration branch, and classifies generated paths as `create`, `keep`, `conflict`, or `invalid`. `apply` publishes non-conflicting files transactionally. Interactive conflict review may publish edited generated content; the default preserves the owner file. Non-interactive conflicts are preserved and make the phase incomplete.

Proposals, completion state, and managed hashes live below `.factory-state/configuration/`. A changed approved stack invalidates an in-memory plan and produces a validation warning after an earlier successful apply. Managed-file drift is a validation error.

## Configurators

| Approved choices | Output | Boundary |
| --- | --- | --- |
| PostgreSQL + Docker Compose | `compose.database.yaml`, `.env.database.example` | Local database service only |
| MySQL + Docker Compose | `compose.database.yaml`, `.env.database.example` | Local database service only |
| MongoDB + Docker Compose | `compose.database.yaml`, `.env.database.example` | Local database service only |
| GitHub Actions | `.github/workflows/factory-verify.yml` | Runtime setup, dependency install, and full Factory verification |
| GitLab CI | `.gitlab-ci.yml` | Runner runtime contract, dependency install, and full Factory verification |

The GitHub Actions workflow checks out submodules, installs the Factory CLI from `.factory`, and adds official runtime setup for approved Node, Java, .NET, or Go source stacks. For Flutter it clones the official stable SDK into the ephemeral runner rather than trusting a third-party setup action; projects that require exact reproducibility should review and pin an SDK revision. The workflow targets the integration branch stored in `.factory-state/factory.yaml`.

GitLab runners vary by executor and are owner-operated infrastructure. Factory therefore records required runtimes in `.gitlab-ci.yml` and refuses to bootstrap global tools or modify the runner. The generated job creates a temporary Python environment for the Factory CLI, then runs the same dependency and full verification boundary. Both submodule and copy link modes include the installable CLI; older partial Factory copies must be updated or re-imported before CI configuration can be published.

## Intentional Boundaries

Database configuration publishes a portable `DATABASE_URL` connection contract but does not modify application source, choose drivers or ORMs, create migrations, provision cloud databases, or write production credentials. The environment example contains local placeholders that must be replaced outside version control for real environments. When a backend and service database are both approved, `stack plan` explicitly reports that driver/ORM approval is still required.

The CI configurators do not configure deployment, registry credentials, environments, branch protection, or provider secrets. `stack plan` reports approved cloud/deployment choices as specification-only until project input includes the required account, region, network, runtime, state, rollout, rollback, and credential decisions. Factory does not create production-impacting infrastructure from underspecified high-level choices.
