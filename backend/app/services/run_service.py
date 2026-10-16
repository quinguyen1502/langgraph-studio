"""Run lifecycle: resolve what to run, execute it off-thread with cancel/timeout, persist history.

Transport-agnostic: the WebSocket controller passes `send(ev)` and `listen()` callables.
"""
import asyncio, json, threading, time, uuid
from dataclasses import dataclass
from typing import Awaitable, Callable, Iterator, Optional
from ..core import config
from ..core.errors import CATALOG, AppError
from ..engine import repo_import
from ..engine.errors import ValidationError
from ..engine.limits import cap_event, cap_run, safe_error, size
from ..engine.runtime import run_stream
from ..models import Run
from ..repositories import RunRepository, WorkflowRepository
from .run_bus import InMemoryRunBus, RunBus
from .telemetry import Telemetry, summarize, trace_url


@dataclass
class RunPlan:
    workflow_id: Optional[str]
    workflow: dict
    input: dict
    resolve: Optional[Callable[[str], dict]] = None  # credential lookup bound to the run's user
    # resuming a waiting run (TASK-0006): same run id, earlier events, {node, value, state}
    run_id: Optional[str] = None
    previous: Optional["Run"] = None
    resume: Optional[dict] = None

    @property
    def imported(self) -> bool:
        return (self.workflow.get("source") or {}).get("kind") == "langgraph_import"

    def events(self) -> Iterator[dict]:
        if self.imported: return repo_import.run_imported(self.workflow, dict(self.input))
        return run_stream(self.workflow, self.input, self.resolve, self.resume)


def error_event(error: dict, **extra) -> dict:
    """WebSocket error event: structured `error` {code, message, details?} plus the legacy `errors` list."""
    details = error.get("details")
    return {"type": "error", **extra, "error": error,
            "errors": details if isinstance(details, list) and details else [error["message"]]}


def _normalise(ev: dict) -> dict:
    """Give engine/sandbox error events (which only carry `errors`) the structured `error` field."""
    if ev.get("type") != "error" or "error" in ev: return ev
    msgs = ev.get("errors") or [CATALOG["RUN_FAILED"][1]]
    code = ev.pop("code", None) or ("NODE_FAILED" if ev.get("node") else "RUN_FAILED")
    ev["error"] = {"code": code, "message": msgs[0], **({"details": msgs} if len(msgs) > 1 else {})}
    return ev


RESPONSE_MAX = 10_000  # characters of a human response
CANCEL_API = object()  # worker -> loop marker: the bus reported a cancel request


def _dumps(x) -> str: return json.dumps(x, ensure_ascii=False, default=str)


class RunService:
    def __init__(self, workflows: WorkflowRepository, runs: RunRepository, credentials=None, bus: RunBus | None = None,
                 telemetry: Telemetry | None = None):
        """credentials: CredentialService (optional; without it, nodes with credential_id fail clearly).
        bus: RunBus for cross-process cancel + event fan-out (in-memory when not given)."""
        self.workflows, self.runs, self.credentials = workflows, runs, credentials
        self.bus = bus or InMemoryRunBus()
        self.telemetry = telemetry or Telemetry(exporters=[])  # no-op unless an exporter is configured

    # ---- cancel from any API process (POST /api/runs/{id}/cancel) ----
    def cancel(self, rid: str, uid: str) -> None:
        if self.bus.owner(rid) is None and self.runs.get(rid) is not None:  # not running here or elsewhere: maybe waiting
            return self.cancel_waiting(rid, uid)
        if self.bus.owner(rid) != uid: raise AppError("RUN_NOT_FOUND")  # unknown, finished or not yours
        self.bus.request_cancel(rid)

    # ---- planning / validation of the client request ----
    def plan(self, uid: str, req) -> RunPlan:
        if not isinstance(req, dict): raise AppError("RUN_REQUEST_INVALID")
        if req.get("resume_run_id"): return self.plan_resume(uid, req["resume_run_id"], req.get("response"))
        wid = req.get("workflow_id"); row = None
        if wid:
            row = self.workflows.get_owned(wid, uid)
            if row is None: raise AppError("WORKFLOW_NOT_FOUND")
        inp = req.get("input", {})
        if not isinstance(inp, dict): raise AppError("RUN_INPUT_INVALID")
        if size(inp) > config.input_max(): raise AppError("RUN_INPUT_TOO_LARGE", max_kb=config.input_max() // 1024)
        stored = json.loads(row.data or "{}") if row else {}
        wf = stored if stored.get("source") else (req.get("workflow") or stored)
        if not isinstance(wf, dict) or size(wf) > config.workflow_max(): raise AppError("WORKFLOW_TOO_LARGE", max_kb=config.workflow_max() // 1024)
        return RunPlan(wid, wf, inp, self.credentials.resolver(uid) if self.credentials else None)

    # ---- human-in-the-loop (TASK-0006) ----
    def waiting_run(self, rid: str, uid: str) -> Run:
        r = self.runs.get(rid)
        if r is None or r.owner != uid: raise AppError("RUN_NOT_FOUND")  # owner only (DEC-0013)
        if r.status != "waiting" or not r.checkpoint: raise AppError("RUN_NOT_WAITING")
        return r

    def plan_resume(self, uid: str, rid: str, response) -> RunPlan:
        if isinstance(response, bool): response = "approved" if response else "rejected"
        if not isinstance(response, str) or len(response) > RESPONSE_MAX: raise AppError("RUN_RESPONSE_INVALID", max=RESPONSE_MAX)
        r = self.waiting_run(rid, uid); cp = json.loads(r.checkpoint)
        return RunPlan(r.workflow_id if r.workflow_id != "adhoc" else None, cp["workflow"], json.loads(r.input or "{}"),
                       self.credentials.resolver(uid) if self.credentials else None,
                       run_id=rid, previous=r, resume={"node": cp["node"], "state": cp["state"], "value": response})

    def pending(self, uid: str) -> list[dict]:
        """Runs of this user waiting for a human response (newest first)."""
        out = []
        for r in self.runs.list_waiting(uid):
            ev = next((e for e in reversed(json.loads(r.events or "[]")) if e.get("type") == "run_waiting"), {})
            w = self.workflows.get(r.workflow_id) if r.workflow_id and r.workflow_id != "adhoc" else None
            out.append({"id": r.id, "workflow_id": r.workflow_id, "workflow_name": w.name if w else None, "node": ev.get("node"),
                        "label": ev.get("label"), "prompt": ev.get("prompt"), "started": r.started, "waiting_since": r.ended})
        return out

    def cancel_waiting(self, rid: str, uid: str) -> None:
        r = self.waiting_run(rid, uid); events = json.loads(r.events or "[]")
        events.append({"type": "run_cancelled", "ts": time.time(), "reason": "api"})
        self.record(rid, r.workflow_id, json.loads(r.input or "{}"), events, None, "cancelled", r.started, uid)

    # ---- history ----
    def history(self, wid: str, uid: str) -> list[dict]:
        if self.workflows.get_owned(wid, uid) is None: raise AppError("WORKFLOW_NOT_FOUND")
        return [{"id": r.id, "workflow_id": r.workflow_id, "input": json.loads(r.input or "null"), "events": json.loads(r.events or "[]"),
                 "final_state": json.loads(r.final_state or "null"), "status": r.status, "started": r.started, "ended": r.ended,
                 "metrics": None if r.duration_ms is None else {"duration_ms": r.duration_ms, "tokens_in": r.tokens_in, "tokens_out": r.tokens_out,
                                                                "tokens": (r.tokens_in or 0) + (r.tokens_out or 0), "cost_usd": r.cost_usd, "error_count": r.error_count},
                 "trace_id": r.trace_id, "trace_url": trace_url(r.trace_id)}
                for r in self.runs.list_for_workflow(wid)]

    def record(self, rid, wid, inp, events, final, status, t0, uid: str = "", checkpoint: dict | None = None) -> dict:
        """Persist the run with its summary metrics and emit its trace. Returns {metrics, trace_id, trace_url}.
        A waiting run keeps its checkpoint and gets its (single) trace only once it ends."""
        t1 = time.time(); metrics = summarize(events, t0, t1)  # from the full events, before capping
        trace_id = None
        if status != "waiting":
            try: trace_id = self.telemetry.record_run({"id": rid, "workflow_id": wid, "owner": uid, "status": status, "started": t0, "ended": t1}, events, metrics)
            except Exception: trace_id = None  # tracing must never fail a run
        events = cap_run([cap_event(e) for e in events])
        final = cap_event({"state": final})["state"] if final is not None else None
        self.runs.add(Run(id=rid, workflow_id=wid or "adhoc", input=_dumps(inp), events=_dumps(events),
                          final_state=_dumps(final), status=status, started=t0, ended=t1, trace_id=trace_id, owner=uid or None,
                          checkpoint=_dumps(checkpoint) if checkpoint else None, **metrics))
        return {"metrics": {**metrics, "tokens": metrics["tokens_in"] + metrics["tokens_out"]}, "trace_id": trace_id, "trace_url": trace_url(trace_id)}

    # ---- execution ----
    async def execute(self, plan: RunPlan, send: Callable[[dict], Awaitable[bool]],
                      listen: Callable[[], Awaitable[str]], uid: str = "") -> str:
        """Stream events through `send` (returns False once the client is gone). `listen` resolves to
        "cancelled" or "disconnected"; a cancel can also arrive through the RunBus (reason "api").
        Returns the final status: ok | error | cancelled | timeout."""
        rid = plan.run_id or uuid.uuid4().hex[:10]; self.bus.start(rid, uid)  # registered so REST/other workers can cancel it
        try: return await self._execute(rid, plan, send, listen, uid)
        finally: self.bus.finish(rid)

    async def _execute(self, rid, plan, send, listen, uid) -> str:
        t0 = time.time(); events: list = []; final = None; status = "ok"; connected = True; bus = self.bus; checkpoint = None
        prev = plan.previous; started = prev.started if prev else t0
        if prev: events.extend(json.loads(prev.events or "[]"))  # resumed: one run, one event log
        q: asyncio.Queue = asyncio.Queue(); loop = asyncio.get_running_loop(); cancel = threading.Event()

        def put(x):
            try: loop.call_soon_threadsafe(q.put_nowait, x)
            except RuntimeError: pass  # loop closed after client went away

        def worker():
            g = None
            try:
                g = plan.events()
                for ev in g:
                    if cancel.is_set(): break  # cooperative cancel between steps
                    if bus.is_cancelled(rid): put(CANCEL_API); break  # cancel requested via REST / another worker
                    put(ev)
            except ValidationError as e:
                put(error_event(AppError("WORKFLOW_INVALID", details=e.errors).to_dict()))
            except AppError as e:
                put(error_event(e.to_dict()))
            except Exception as e:
                put(error_event({"code": "RUN_FAILED", "message": safe_error(e)}))
            finally:
                if g is not None:
                    try: g.close()  # stops LangGraph stream / kills import subprocess
                    except Exception: pass
                put(None)

        async def emit(ev):
            nonlocal connected
            events.append(ev)
            try: bus.publish(rid, ev)
            except Exception: pass  # fan-out is best effort; the socket and history stay authoritative
            if connected: connected = await send(cap_event(ev))

        try:
            await emit({"type": "run_resumed" if prev else "run_started", "run_id": rid, "ts": t0,
                        **({"node": plan.resume["node"], "response": plan.resume["value"]} if prev else {})})
            threading.Thread(target=worker, daemon=True).start()
            listener = asyncio.create_task(listen()); deadline = t0 + config.run_timeout(); ended = None
            while True:
                get = asyncio.ensure_future(q.get())
                done, _ = await asyncio.wait({get, listener}, timeout=max(0.0, deadline - time.time()), return_when=asyncio.FIRST_COMPLETED)
                if get in done:
                    ev = get.result()
                    if ev is None: break
                    if ev is CANCEL_API: ended = "api"; cancel.set(); break
                    ev = _normalise(ev); ev["ts"] = time.time()
                    if ev["type"] == "run_finished": final = ev.get("state")
                    if ev["type"] == "error": status = "error"
                    if ev["type"] == "run_waiting": status = "waiting"; checkpoint = {**ev.pop("checkpoint"), "workflow": plan.workflow}
                    await emit(ev); continue
                get.cancel()
                if listener in done:
                    ended = listener.result(); connected = connected and ended == "cancelled"
                else:
                    ended = "timeout"
                cancel.set(); break
            if not listener.done(): listener.cancel()
            if ended in ("cancelled", "disconnected", "api"):
                status = "cancelled"
                reason = {"cancelled": "client", "disconnected": "disconnect"}.get(ended, "api")
                await emit({"type": "run_cancelled", "ts": time.time(), "reason": reason})
            elif ended == "timeout":
                status = "timeout"
                await emit(error_event(AppError("RUN_TIMEOUT", seconds=f"{config.run_timeout():g}").to_dict(), status="timeout", ts=time.time()))
        except asyncio.CancelledError:  # handler cancelled (server shutdown / client gone mid-await): still keep history
            cancel.set(); status = "cancelled"
            events.append({"type": "run_cancelled", "ts": time.time(), "reason": "disconnect"})
            await asyncio.shield(asyncio.to_thread(self.record, rid, plan.workflow_id, plan.input, events, final, status, started, uid, None))
            raise
        summary = await asyncio.to_thread(self.record, rid, plan.workflow_id, plan.input, events, final, status, started, uid, checkpoint)
        if connected: await send({"type": "run_summary", "run_id": rid, "status": status, "ts": time.time(), **summary})  # not stored as an event
        return status
