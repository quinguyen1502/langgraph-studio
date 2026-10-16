# Decision Record

## Metadata

- Project: langgraph-studio
- Decision ID: DEC-0012
- Status: Accepted
- Owner: Thái Quí Nguyễn
- Created: 2026-10-16
- Updated: 2026-10-16
- Related Requirements: REQ-0010
- Related Architecture: ARCH-0001
- Related Tasks: TASK-0010

## Context

REQ-0010 open question: "LangSmith, OTel collector, or both?"

## Decision

**Both, with OpenTelemetry as the standard.** LangSmith is one more OTLP destination, not a second integration.

1. One code path: `services/telemetry.Telemetry` builds an OTel `TracerProvider` (its own, never the global one) with one span exporter per configured destination.
   - **OTLP**: enabled when `OTEL_EXPORTER_OTLP_ENDPOINT` or `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` is set. All standard `OTEL_*` variables apply (headers, timeout, `OTEL_SERVICE_NAME`, `OTEL_TRACES_EXPORTER=none`, `OTEL_SDK_DISABLED=true`).
   - **LangSmith**: enabled only when `LANGSMITH_API_KEY` is set **and** `LANGSMITH_TRACING` is true. Spans go to `${LANGSMITH_ENDPOINT:-https://api.smith.langchain.com}/otel/v1/traces` with `x-api-key` (and `Langsmith-Project` from `LANGSMITH_PROJECT`).
   - **Neither**: a clean no-op. The SDK is not imported, no trace id is stored, no link is shown.
2. **Trace shape**: one trace per run. The root span `run` carries run id, workflow id, user id, status, error count, tokens and cost. Each executed node gets one child span, `node <label>`, with duration, OK/ERROR status, an `exception` event on errors, and for LLM nodes the `gen_ai.*` token attributes plus `studio.cost_usd`.
3. **Built after the run** from the event timestamps (`ts`, `duration_ms`). The engine has no tracing code; exporting never fails a run.
4. **Metrics persisted per run** (migration `0003_run_metrics`): `duration_ms`, `tokens_in`, `tokens_out`, `cost_usd`, `error_count`, `trace_id`. They are sent live as a final `run_summary` WebSocket event and returned in run history.
5. **Cost** comes from a small price table (`engine/usage.PRICES`, USD per 1M tokens, longest prefix wins). Unknown models get `cost_usd = null`. Mock runs report estimated tokens (~4 chars/token) and cost 0, so offline mode works without keys.
6. **Trace link**: `STUDIO_TRACE_URL` template (e.g. `http://localhost:16686/trace/{trace_id}` for the compose Jaeger profile).

## Consequences

- Spans reach the backend when the run ends (no live spans for long runs).
- If `LANGSMITH_TRACING=true` is set, LangChain's own LangSmith tracer may also trace the LangGraph run natively (duplicate, differently shaped runs). See REV-0009.
