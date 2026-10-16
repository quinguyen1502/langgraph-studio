# Approval Gates

Approval gates protect work that is destructive, irreversible, broad in scope, security-sensitive, or operationally risky.

## Require Human Approval Before

- Deleting or overwriting durable project data.
- Removing source files, artifacts, history, or configuration outside the approved task scope.
- Running destructive commands or migrations.
- Changing credentials, secrets, permissions, or security boundaries.
- Changing production, release, deployment, rollback, or operational flows.
- Adding, removing, or replacing major dependencies, frameworks, platforms, or architecture patterns.
- Performing broad rewrites or automated changes across many files.
- Accepting unresolved blocking review or QA findings.
- Merging an implementation task branch into the project integration branch, normally `develop`.

## Branch And Pull Request Gate

Factory-managed implementation work must use a branch and pull request gate by default:

- Start each task from the project integration branch, normally `develop`.
- Create one branch per task, normally `factory/task-<id>-<short-name>`.
- Commit only the task-scoped source and artifact changes on that branch.
- Run and record required validation before requesting review.
- Push the task branch and open one Draft PR into the integration branch when
  the task enters review.
- Keep owner feedback, review, QA, and rework on the same branch and Draft PR.
- After owner review and QA pass, update final artifacts and move the task to
  done before creating the final single task commit.
- Rebase onto the latest integration branch, squash the task into one commit,
  rerun required validation, and push with `--force-with-lease`.
- Mark the existing Draft PR Ready for review; do not create a replacement PR.
- Wait for explicit human approval before merging the pull request.

Agents may merge directly only when the human owner explicitly asks for a merge in the current task context. When pull request tooling, network access, or repository permissions are unavailable for an active delivery task, agents must document the blocker and leave the task on a committed branch rather than merging into the integration branch.

Prefer a rebase merge when the hosting platform supports it so the integration
branch remains linear and each task contributes one commit. Do not create a
merge commit by default. Use squash merge only when the human owner explicitly
chooses it. Never use an unrestricted force push.

Do not promote local execution mechanics into project blockers when no active delivery task is blocked. Missing CLI authentication, sandbox retries, package index hiccups, or exploratory command failures should be summarized to the owner or recorded in the current task activity log only when relevant.

Dependent tasks should be based on the integration branch after the prior pull request has merged. If a task must be stacked on an unmerged branch, document the dependency in the task artifact and pull request.

## Approval Record

Record approvals in the relevant artifact with:

- What was approved.
- Who approved it.
- When it was approved.
- Scope and limits of the approval.
- Related risks or rollback notes.

## If Approval Is Missing

Stop the risky action, document the blocker, and return the task to the appropriate lifecycle state.
