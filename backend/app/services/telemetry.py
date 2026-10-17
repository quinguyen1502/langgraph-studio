"""Run telemetry (TASK-0010, DEC-0012): per-run summary metrics + OpenTelemetry traces.

- `summarize(events, ...)` -> the metrics persisted on each run (duration, tokens, cost, error count).
- `Telemetry` turns a finished run's events into one trace: a root `run` span and one span per node
  (duration, status, error, gen_ai token usage, cost). Spans are built after the run from event
  timestamps, so the engine stays unaware of tracing.
- Exporters come from standard env: OTLP via OTEL_EXPORTER_OTLP_(TRACES_)ENDPOINT / OTEL_* and,
  optionally, LangSmith (its OTLP endpoint) when LANGSMITH_API_KEY is set and LANGSMITH_TRACING is true.
  With none configured (or OTEL_SDK_DISABLED=true) tracing is a no-op and the SDK is never imported.
"""
from __future__ import annotations
import os
from typing import Any, Optional

TRUE = ("1", "true", "yes", "on")
LANGSMITH_DEFAULT = "https://api.smith.langchain.com"


def summarize(events: list[dict], started: float, ended: float) -> dict:
    """Per-run summary metrics from the run's events (the same numbers the UI and the trace show)."""
    tin = tout = errors = 0; cost: Optional[float] = 0.0; llm = False
    waited = waited_s(events, ended)
    for ev in events:
        if ev.get("type") == "error": errors += 1
        u = ev.get("usage")
        if ev.get("type") == "node_finished" and u:
            llm = True; tin += u.get("tokens_in", 0); tout += u.get("tokens_out", 0)
            cost = None if cost is None or u.get("cost_usd") is None else cost + u["cost_usd"]
    return {"duration_ms": round(max(0.0, ended - started - waited) * 1000, 2), "tokens_in": tin, "tokens_out": tout,
            "cost_usd": (round(cost, 8) if cost is not None else None) if llm else 0.0, "error_count": errors}


def waited_s(events: list[dict], ended: float) -> float:
    """Seconds spent paused at Human nodes: from each `run_waiting` to the next event (resume/cancel/expiry).
    A run that is still waiting has no wait counted yet (its duration is the active time so far)."""
    total = 0.0; since = None
    for ev in events:
        if since is not None and ev.get("ts"):
            total += max(0.0, ev["ts"] - since); since = None
        if ev.get("type") == "run_waiting" and ev.get("ts"): since = ev["ts"]
    return total + (max(0.0, ended - since) if since is not None else 0.0)


def _env(name: str) -> str: return (os.environ.get(name) or "").strip()


def exporter_configs() -> list[dict]:
    """Which span exporters the environment asks for (pure; no SDK import)."""
    if _env("OTEL_SDK_DISABLED").lower() in TRUE: return []
    out = []
    if (_env("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT") or _env("OTEL_EXPORTER_OTLP_ENDPOINT")) and _env("OTEL_TRACES_EXPORTER").lower() != "none":
        out.append({"name": "otlp"})  # the OTLP exporter reads OTEL_EXPORTER_OTLP_* itself (endpoint, headers, timeout)
    if _env("LANGSMITH_API_KEY") and _env("LANGSMITH_TRACING").lower() in TRUE:
        base = (_env("LANGSMITH_ENDPOINT") or LANGSMITH_DEFAULT).rstrip("/")
        headers = {"x-api-key": _env("LANGSMITH_API_KEY")}
        if _env("LANGSMITH_PROJECT"): headers["Langsmith-Project"] = _env("LANGSMITH_PROJECT")
        out.append({"name": "langsmith", "endpoint": f"{base}/otel/v1/traces", "headers": headers})
    return out


def disable_langchain_tracer() -> None:
    """We export to LangSmith ourselves (OTLP). LANGSMITH_TRACING=true would ALSO switch on LangChain's own
    LangSmith tracer inside nodes, so every LLM call would show up twice. Turn that one off:
    LANGSMITH_TRACING_V2 takes precedence over LANGSMITH_TRACING (and is inherited by import sandboxes),
    and langsmith.configure(enabled=False) covers already-loaded code."""
    os.environ["LANGSMITH_TRACING_V2"] = "false"; os.environ["LANGCHAIN_TRACING_V2"] = "false"
    try:
        import langsmith
        from langsmith import utils as ls_utils
        ls_utils.get_env_var.cache_clear()
        langsmith.configure(enabled=False)
    except Exception:  # langsmith not installed / older API: the env vars are enough
        pass


def trace_url(trace_id: Optional[str]) -> Optional[str]:
    """Link to the trace viewer when STUDIO_TRACE_URL (e.g. http://localhost:16686/trace/{trace_id}) is set."""
    tpl = _env("STUDIO_TRACE_URL")
    return tpl.replace("{trace_id}", trace_id) if tpl and trace_id else None


def _ns(seconds: float) -> int: return int(seconds * 1e9)


class Telemetry:
    """Built once per process (api.deps.get_telemetry). `exporters` lets tests inject an in-memory exporter."""

    def __init__(self, exporters: Optional[list] = None, sync: bool = False):
        self._tracer = None; self._provider = None
        if exporters is None: exporters = self._from_env()
        if not exporters: return  # no-op
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor
        res = Resource.create({"service.name": _env("OTEL_SERVICE_NAME") or "langgraph-studio"})
        self._provider = TracerProvider(resource=res)  # own provider: never touches the global one
        for ex in exporters: self._provider.add_span_processor(SimpleSpanProcessor(ex) if sync else BatchSpanProcessor(ex))
        self._tracer = self._provider.get_tracer("langgraph-studio")
        self.exporters = [type(e).__name__ for e in exporters]

    @staticmethod
    def _from_env() -> list:
        cfgs = exporter_configs()
        if not cfgs: return []
        if any(c["name"] == "langsmith" for c in cfgs): disable_langchain_tracer()
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        return [OTLPSpanExporter() if c["name"] == "otlp" else OTLPSpanExporter(endpoint=c["endpoint"], headers=c["headers"])
                for c in cfgs]

    @property
    def enabled(self) -> bool: return self._tracer is not None

    def flush(self) -> None:
        if self._provider: self._provider.force_flush()

    def record_run(self, run: dict, events: list[dict], metrics: dict) -> Optional[str]:
        """Emit the run's trace; returns the trace id (32 hex chars) or None when disabled."""
        if not self.enabled: return None
        from opentelemetry import trace
        from opentelemetry.trace import Status, StatusCode
        t = self._tracer; ok = run["status"] == "ok"  # noqa: E702
        root = t.start_span("run", start_time=_ns(run["started"]), attributes={
            "studio.run.id": run["id"], "studio.workflow.id": run.get("workflow_id") or "adhoc", "studio.user.id": run.get("owner") or "",
            "studio.run.status": run["status"], "studio.run.error_count": metrics["error_count"],
            "gen_ai.usage.input_tokens": metrics["tokens_in"], "gen_ai.usage.output_tokens": metrics["tokens_out"],
            **({"studio.cost_usd": metrics["cost_usd"]} if metrics["cost_usd"] is not None else {})})
        ctx = trace.set_span_in_context(root)
        for ev in events:
            kind = ev.get("type")
            if kind not in ("node_finished", "error") or not ev.get("node"): continue
            end = ev.get("ts") or run["ended"]; start = end - (ev.get("duration_ms") or 0) / 1000
            attrs: dict[str, Any] = {"studio.node.id": ev["node"], "studio.node.type": ev.get("node_type") or "",
                                     "studio.node.label": ev.get("label") or "", "studio.node.iteration": ev.get("iteration") or 1,
                                     "studio.node.duration_ms": ev.get("duration_ms") or 0}
            if (u := ev.get("usage")):
                attrs.update({"gen_ai.system": u["provider"], "gen_ai.request.model": u["model"],
                              "gen_ai.usage.input_tokens": u["tokens_in"], "gen_ai.usage.output_tokens": u["tokens_out"],
                              "studio.usage.estimated": u["estimated"]})
                if u["cost_usd"] is not None: attrs["studio.cost_usd"] = u["cost_usd"]
            span = t.start_span(f"node {ev.get('label') or ev['node']}", context=ctx, start_time=_ns(start), attributes=attrs)
            if kind == "error":
                err = ev.get("error") or {}
                span.set_status(Status(StatusCode.ERROR, err.get("message") or ""))
                span.add_event("exception", {"exception.type": err.get("code") or "NODE_FAILED", "exception.message": err.get("message") or ""})
            else:
                span.set_status(Status(StatusCode.OK))
            span.end(end_time=_ns(end))
        if ok: root.set_status(Status(StatusCode.OK))
        elif run["status"] in ("error", "timeout"): root.set_status(Status(StatusCode.ERROR, run["status"]))  # cancelled stays UNSET
        root.end(end_time=_ns(run["ended"]))
        return format(root.get_span_context().trace_id, "032x")
