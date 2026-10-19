# Requirement

## Metadata

- Project: langgraph-studio
- Requirement ID: REQ-0010
- Status: Implemented
- Owner: Thái Quí Nguyễn
- Created: 2026-10-16
- Updated: 2026-10-19
- Source: project-specs.md (Post-MVP Scope)

## Summary

Run tracing and observability. Runs emit structured traces and metrics (LangSmith and/or OpenTelemetry) and the UI links to them.

## Problem Or Opportunity

Runs emit structured traces and metrics (LangSmith and/or OpenTelemetry) and the UI links to them.

## Scope

### In Scope

- Per-node spans, token/cost capture, error rates
- Optional LangSmith export

### Out Of Scope

- Full APM dashboards

## Stakeholders Or Users

- Internal developers and learners using LangGraph Studio
- Project owner (administrator)

## Current Context

- Run events only stored as JSON in `runs` table

## Desired Behavior

Runs emit structured traces and metrics (LangSmith and/or OpenTelemetry) and the UI links to them.

## Business Rules

- None

## Constraints

- Mock/offline mode must keep working without API keys.
- Must not break existing auth/ownership rules.

## Acceptance Criteria

- Each run produces a trace with one span per node including duration and status
- Tracing is disabled cleanly when no exporter is configured

## Edge Cases

- Missing credentials or unavailable external services produce clear `error` events.

## Assumptions

- Stack direction in `project-specs.md` (Preferred) remains in place.

## Open Questions

- Resolved 2026-10-16: both, with OpenTelemetry as the standard: OTLP when `OTEL_EXPORTER_OTLP_*` is set, and LangSmith as one more OTLP destination when `LANGSMITH_API_KEY` and `LANGSMITH_TRACING` are set (DEC-0012).

## Related Artifacts

- `project-specs.md`
- `.factory-state/artifacts/ARCH-0001-current-architecture.md`
- `.factory-state/artifacts/DISC-0001-project-context.md`
- Delivered by `.factory-state/tasks/done/TASK-0010-add-tracing-and-observability-for-runs.md`, merged to `develop`.
