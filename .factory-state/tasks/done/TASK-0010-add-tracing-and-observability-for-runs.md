# Task

## Metadata

- Project: langgraph-studio
- Task ID: TASK-0010
- Previous ID: TASK-0009 (renumbered 2026-10-16, DEC-0007)
- Status: done
- Owner: Grok Bot (agent)
- Created: 2026-10-16
- Updated: 2026-10-16
- Requirement IDs: REQ-0010
- Design IDs: DEC-0012
- Architecture IDs: ARCH-0001

## Objective

Implement REQ-0010: Add tracing and observability for runs.

## Scope

### In Scope

- Deliver the in-scope items of `.factory-state/artifacts/REQ-0010-observability.md`

### Out Of Scope

- Out-of-scope items listed in REQ-0010

## Inputs

- `.factory-state/artifacts/REQ-0010-observability.md`
- `.factory-state/artifacts/ARCH-0001-current-architecture.md`

## Related Artifacts

- Requirement: `.factory-state/artifacts/REQ-0010-observability.md`
- Architecture: `.factory-state/artifacts/ARCH-0001-current-architecture.md`
- Discovery: `.factory-state/artifacts/DISC-0001-project-context.md`

## Expected Outputs

- Implementation, tests, README update
- Design/architecture artifact if the requirement changes boundaries

## Constraints

- Mock mode and existing tests must keep passing

## Dependencies

- TASK-0002 (CI) recommended first

## Acceptance Criteria

- Each run produces a trace with one span per node including duration and status
- Tracing is disabled cleanly when no exporter is configured

## Validation Plan

- `cd backend && .venv/bin/python -m pytest -q`
- `cd frontend && npm run build`
- Manual run of the seeded example

## Assumptions

- Phase 2 integrates into `develop`. This branch is stacked on TASK-0009 (PR #11) because it extends its compose file.

## Open Questions

- LangSmith, OTel collector, or both? **Resolved (DEC-0012): both; OpenTelemetry is the standard, and LangSmith is an optional OTLP destination.**

## Delivered

- Token usage per LLM call (`engine/usage.py`; OpenAI/Anthropic usage from the response; mock usage estimated at cost 0) attached to `node_finished.usage`.
- `services/telemetry.py`: one OTel trace per run (root `run` span + one span per node, with duration, status, error event, gen_ai tokens and cost). OTLP via `OTEL_*`; LangSmith via `LANGSMITH_API_KEY` + `LANGSMITH_TRACING`; no-op otherwise.
- Per-run metrics persisted (migration `0003_run_metrics`), final `run_summary` WS event, `metrics`/`trace_id`/`trace_url` in history; health `tracing` flag.
- UI: tokens, cost, error count and an "Open trace" link in the trace summary; per-span tokens/cost tooltip; tokens/cost/duration in history (en/vi).
- Compose `tracing` profile with Jaeger all-in-one (OTLP in, UI on :16686).
- Tests: `tests/test_telemetry.py`, `e2e/metrics.spec.ts`. Docs: DEC-0012, ARCH-0001, `docs/backend-architecture.md`, README, roadmap, REV-0009, QA-0009.

## Activity Log

- 2026-10-16: Implemented on `factory/task-0010-add-tracing-and-observability-for-runs` (branched from TASK-0009 / PR #11); moved to review.

- 2026-10-16: Renumbered TASK-0009 -> TASK-0010 per owner re-plan (DEC-0007).
- 2026-10-16: Created task during Factory import/onboarding.

- 2026-10-17: Status set to done to match the done/ folder. Previous Status was `review`. Review REV-0009. QA QA-0009.

## Handoff Notes

- Use branch `factory/task-0010-add-tracing-and-observability-for-runs` when implementation begins.
