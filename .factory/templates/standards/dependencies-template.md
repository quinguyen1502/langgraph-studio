# Dependency Selection Standard (Template)

This template describes the shape of a project's dependency selection
standard. Copy it to `.factory-state/standards/dependencies.md` and
fill in project-specific thresholds and ecosystem signals.

## When this applies

- Before adding any new third-party package, plugin, or library to
  the project's manifest.
- Before upgrading a dependency across a major version boundary.
- When a task discovers an unfamiliar package during implementation
  and considers adopting it.

## Approval requirements

Every new or upgraded dependency must be justified against these
criteria before the change is merged:

1. **Stability**. Prefer stable releases. Pre-release versions
   (alpha, beta, release candidates, or ecosystem-specific unstable
   markers) require explicit owner approval recorded in a decision
   artifact.
2. **Maintenance**. The package must be actively maintained. Recent
   publish or release cadence, closed-issue ratio, and responsiveness
   to security reports are all signals.
3. **Provenance**. Prefer packages from verified publishers,
   framework maintainers, or ecosystem-endorsed lists where the
   package registry provides such signals.
4. **Status**. Do not use packages marked discontinued, deprecated,
   archived, or otherwise abandoned by their maintainers.
5. **Platform support**. The package must cover every platform the
   project targets.
6. **License**. Must be compatible with the project's chosen license
   and any downstream distribution constraints.
7. **Necessity**. Prefer standard-library or already-installed
   solutions. If the required code is small and stable, prefer
   writing it in-project rather than adding a new dependency.

If a candidate dependency fails one criterion but is still required,
the exception must be recorded in a decision artifact under
`.factory-state/decisions/` before the dependency is added.

## Project-specific thresholds

Projects instantiate this template with concrete, verifiable
thresholds. Examples of what to fill in:

- Minimum version constraint (for example, ">= 1.0.0" or ecosystem
  equivalent).
- Maximum time since last publish (for example, twelve months).
- Ecosystem-specific quality signals (pub.dev score for Dart, npm
  downloads for Node, crates.io downloads for Rust, PyPI stability
  metadata for Python, and so on).
- Any additional owner-approved allowlist or denylist.

## Recording

- Owner-approved exceptions live in
  `.factory-state/decisions/DEC-####-<slug>.md`.
- Per-task dependency justification lives in the active task activity
  log entries, referencing the decision when applicable.
