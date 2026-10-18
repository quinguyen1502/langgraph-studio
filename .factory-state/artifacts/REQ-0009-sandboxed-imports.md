# Requirement

## Metadata

- Project: langgraph-studio
- Requirement ID: REQ-0009
- Status: Implemented
- Owner: Thái Quí Nguyễn
- Created: 2026-10-16
- Updated: 2026-10-18
- Source: project-specs.md (Post-MVP Scope)

## Summary

Container-sandboxed repo imports. Imported repository code (install, inspect, run) executes inside an isolated container with resource and network limits instead of a host subprocess.

## Problem Or Opportunity

Imported repository code (install, inspect, run) executes inside an isolated container with resource and network limits instead of a host subprocess.

## Scope

### In Scope

- Container runner for install/inspect/run
- CPU/memory/time limits, read-only base, controlled network egress
- Explicit secret injection per run

### Out Of Scope

- Arbitrary language runtimes beyond Python

## Stakeholders Or Users

- Internal developers and learners using LangGraph Studio
- Project owner (administrator)

## Current Context

- `backend/app/importer.py` runs code as the server's OS user in a subprocess (documented risk in README)

## Desired Behavior

Imported repository code (install, inspect, run) executes inside an isolated container with resource and network limits instead of a host subprocess.

## Business Rules

- None

## Constraints

- Mock/offline mode must keep working without API keys.
- Must not break existing auth/ownership rules.

## Acceptance Criteria

- Import and run of `new-langgraph-project` succeed inside the container with identical events
- Imported code cannot read files outside its import directory or the server environment
- A run exceeding limits is killed and reported as an error event

## Edge Cases

- Missing credentials or unavailable external services produce clear `error` events.

## Assumptions

- Stack direction in `project-specs.md` (Preferred) remains in place.

## Open Questions

- Closed 2026-10-18. The owner accepted Docker (OCI `runc`, including Docker Desktop) as the runtime. gVisor and Firecracker stay out of scope.

## Owner Acceptance

- 2026-10-18: Owner approved the behaviour shipped in TASK-0015 (PR #33). Accepted residual risk: with `STUDIO_ENABLE_IMPORT` off, an already imported graph runs in the host subprocess; install always uses network `bridge`; a run defaults to `bridge`.

## Related Artifacts

- `project-specs.md`
- `.factory-state/artifacts/ARCH-0001-current-architecture.md`
- `.factory-state/artifacts/DISC-0001-project-context.md`
