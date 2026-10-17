"""Run lifecycle: resolve what to run, execute it off-thread with cancel/timeout, persist history.

Transport-agnostic: the WebSocket controller passes `send(ev)` and `listen()` callables.
"""
import asyncio, json, threading, time, uuid
from dataclasses import dataclass
from typing import Awaitable, Callable, Iterator, Optional
from ..core import config
from ..core.errors import CATALOG, AppError
from ..engine import repo_import
from ..engine import subgraphs
from ..engine.errors import ValidationError
from ..engine.limits import cap_event, cap_run, safe_error, size
from ..engine.effects import Effects
from ..engine.runtime import resume_nodes, run_stream
from ..models import Run
from ..repositories import RunRepository, StaleLease, WorkflowRepository
from .run_bus import InMemoryRunBus, RunBus
from .telemetry import Telemetry, summarize, trace_url
from ..core.logging import get_logger
from .workflow_diff import same_content


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
    source: str = "ui"  # ui | api (TASK-0007)
    version: Optional[int] = None  # stored workflow version that runs; None = unsaved edits (TASK-0008)
    trace_parent: Optional[dict] = None  # {trace_id, span_id} of the previous trace segment (TASK-0020)
    recovered: bool = False       # continuing a queue job whose worker died (TASK-0020)
    checkpointing: bool = False   # save a progress checkpoint after each node (queue jobs, TASK-0020)
    fence: Optional[int] = None   # lease generation of the queue job (TASK-0021): every write carries it
    attempt: int = 1              # queue delivery attempt, sent to side effects as X-Studio-Attempt
    effects: Optional[Effects] = None  # idempotency keys / ledger / fencing guard, set by RunService._execute
    resumed_by: Optional[dict] = None  # {channel, user_id} when an approval channel answered (TASK-0022)
    invalid: Optional[list] = None  # subgraph reference errors found while planning (TASK-0011), reported as WORKFLOW_INVALID

    @property
    def imported(self) -> bool:
        return (self.workflow.get("source") or {}).get("kind") == "langgraph_import"

    def events(self) -> Iterator[dict]:
        if self.imported: return repo_import.run_imported(self.workflow, dict(self.input), resume=self.resume, checkpointing=self.checkpointing)
        if self.invalid: raise ValidationError(self.invalid)
        return run_stream(self.workflow, self.input, self.resolve, self.resume, self.effects)


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
log = get_logger("runs")
CANCEL_API = object()  # worker -> loop marker: the bus reported a cancel request
FENCED = object()      # worker -> loop marker: another worker claimed this run (stale lease, TASK-0021)
RESUME_KEYS = ("node", "nodes", "state", "counts", "blob")  # what a progress checkpoint stores to continue from


class _RunLedger:
    """Ledger adapter for one run (engine.effects.Ledger): JSON in the node_results table, fenced writes."""
    def __init__(self, repo, rid: str, fence: Optional[int]): self.repo, self.rid, self.fence = repo, rid, fence
    def get(self, nid, it):
        row = self.repo.get(self.rid, nid, it)
        return json.loads(row.delta) if row else None
    def put(self, nid, it, delta, key): self.repo.put(self.rid, nid, it, _dumps(delta), key, self.fence)


def _dumps(x) -> str: return json.dumps(x, ensure_ascii=False, default=str)


class RunService:
    def __init__(self, workflows: WorkflowRepository, runs: RunRepository, credentials=None, bus: RunBus | None = None,
                 telemetry: Telemetry | None = None, versions=None, notifier=None, ledger=None, approvals=None,
                 deliveries: Optional[Callable[[], object]] = None):
        """credentials: CredentialService (optional; without it, nodes with credential_id fail clearly).
        bus: RunBus for cross-process cancel + event fan-out (in-memory when not given)."""
        self.workflows, self.runs, self.credentials = workflows, runs, credentials
        self.bus = bus or InMemoryRunBus()
        self.versions = versions  # WorkflowVersionRepository (optional): tags runs with the version they ran
        self.telemetry = telemetry or Telemetry(exporters=[], metric_readers=[])  # no-op unless an exporter is configured
        self.notifier = notifier  # NotificationService (optional): in-app/e-mail/webhook when a run waits or expires (TASK-0020)
        self.ledger = ledger      # NodeResultRepository (optional): node-result ledger of queue jobs (TASK-0021)
        self.deliveries = deliveries  # -> DeliveryService (optional): callback_url webhook when an API run settles
        self.approvals = approvals  # ApprovalService (optional): Slack/Telegram approval requests of Human nodes (TASK-0022)

    # ---- cancel from any API process (POST /api/runs/{id}/cancel) ----
    def cancel(self, rid: str, uid: str) -> None:
        row = self.runs.get(rid) if self.bus.owner(rid) is None else None  # not running here or elsewhere
        if row is not None and row.status == "queued" and row.owner == uid:  # API run not picked up yet: worker skips it
            return self.runs.set_status(rid, "cancelled")
        if row is not None: return self.cancel_waiting(rid, uid)
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
        version = self._version_of(wid, wf)
        wf, invalid = self._expand(uid, wid, wf)
        return RunPlan(wid, wf, inp, self.credentials.resolver(uid) if self.credentials else None, version=version, invalid=invalid)

    def _expand(self, uid: str, wid: Optional[str], wf: dict) -> tuple[dict, Optional[list]]:
        """Inline subgraph nodes (TASK-0011) with the workflows this user may read. The expanded graph is what runs and
        what checkpoints store, so a resumed or recovered run continues on the same graph even if a child changed."""
        if wf.get("source") or not subgraphs.has_subgraphs(wf): return wf, None
        try: return subgraphs.expand(wf, self.workflow_loader(uid), wid), None
        except ValidationError as e: return wf, e.errors

    def workflow_loader(self, uid: str):
        def load(ref: str) -> Optional[dict]:
            row = self.workflows.get_owned(ref, uid)
            return json.loads(row.data or "{}") if row else None
        return load

    def _version_of(self, wid, wf: dict) -> Optional[int]:
        """The latest stored version number if `wf` matches it in content, else None (unsaved edits)."""
        if not wid or self.versions is None: return None
        v = self.versions.latest(wid)
        return v.version if v and same_content(json.loads(v.data or "{}"), wf) else None

    # ---- human-in-the-loop (TASK-0006) ----
    def waiting_run(self, rid: str, uid: str) -> Run:
        r = self.runs.get(rid)
        if r is None or r.owner != uid: raise AppError("RUN_NOT_FOUND")  # owner only (DEC-0013)
        if r.status != "waiting" or not r.checkpoint: raise AppError("RUN_NOT_WAITING")
        if self._is_stale(r): self._expire(r); raise AppError("RUN_EXPIRED")
        return r

    @staticmethod
    def _is_stale(r: Run, now: float | None = None) -> bool:
        ttl = config.wait_ttl()
        return bool(ttl) and (r.ended or r.started or 0) < (now or time.time()) - ttl

    def _close_waiting(self, r: Run, ev: dict, status: str, uid: str) -> None:
        """End a waiting run without executing it (cancel / expiry): one more trace segment, no node spans."""
        cp = json.loads(r.checkpoint or "{}")
        self.record(r.id, r.workflow_id, json.loads(r.input or "{}"), json.loads(r.events or "[]") + [ev], None, status, r.started, uid,
                    source=r.source or "ui", version=r.workflow_version, trace_parent=cp.get("trace"), trace_events=[] if cp.get("trace") else None)

    def _expire(self, r: Run) -> None:
        self._close_waiting(r, {"type": "run_expired", "ts": time.time(), "ttl_s": config.wait_ttl()}, "expired", r.owner or "")

    def expire_waiting(self) -> int:
        """Expire runs that waited longer than STUDIO_WAIT_TTL (periodic sweep + lazily on access). Returns the count."""
        ttl = config.wait_ttl()
        if not ttl: return 0
        stale = self.runs.list_waiting_before(time.time() - ttl)
        for r in stale: self._expire(r)
        return len(stale)

    def plan_resume(self, uid: str, rid: str, response, via_channel: bool = False) -> RunPlan:
        if isinstance(response, bool): response = "approved" if response else "rejected"
        if not isinstance(response, str) or len(response) > RESPONSE_MAX: raise AppError("RUN_RESPONSE_INVALID", max=RESPONSE_MAX)
        r = self.waiting_run(rid, uid); cp = json.loads(r.checkpoint)
        if self.approvals is not None and not via_channel:  # answered in the studio: the channel buttons stop working (TASK-0022)
            if self.approvals.decided_elsewhere(rid): raise AppError("RUN_NOT_WAITING")
            self.approvals.close_run(rid, "answered")
        return RunPlan(r.workflow_id if r.workflow_id != "adhoc" else None, cp["workflow"], json.loads(r.input or "{}"),
                       self.credentials.resolver(uid) if self.credentials else None,
                       run_id=rid, previous=r, resume={**{k: cp[k] for k in RESUME_KEYS if k in cp}, "value": response}, source=r.source or "ui",
                       version=r.workflow_version, trace_parent=cp.get("trace"))

    def plan_recover(self, r: Run, fence: Optional[int] = None, attempt: int = 2) -> RunPlan:
        """A recovered queue job (its worker died or lost its lease mid-run). With a progress checkpoint it continues
        from there (same checkpoint shape as HITL; parallel branches and imported graphs included, TASK-0021);
        without one it starts over. Either way the lost segment's root span is exported first (DEC-0018)."""
        cp = json.loads(r.checkpoint or "null") or {}
        if cp.get("kind") != "progress": cp = {}
        lost = cp.get("trace")
        if lost:
            try: self.telemetry.close_lost(lost, cp.get("ts") or time.time())
            except Exception: log.warning("exporting the lost segment of run %s failed", r.id)
        common = dict(run_id=r.id, source=r.source or "api", trace_parent=lost, checkpointing=True, fence=fence, attempt=attempt)
        if not (cp.get("node") or cp.get("nodes")):  # nothing finished yet: restart from the beginning
            plan = self.plan(r.owner or "", {"workflow_id": r.workflow_id, "input": json.loads(r.input or "{}")})
            for k, v in common.items(): setattr(plan, k, v)
            return plan
        return RunPlan(r.workflow_id if r.workflow_id != "adhoc" else None, cp["workflow"], json.loads(r.input or "{}"),
                       self.credentials.resolver(r.owner) if self.credentials else None, previous=r,
                       resume={k: cp[k] for k in RESUME_KEYS if k in cp}, version=r.workflow_version, recovered=True, **common)

    def pending(self, uid: str) -> list[dict]:
        """Runs of this user waiting for a human response (newest first)."""
        out = []; self.expire_waiting()
        for r in self.runs.list_waiting(uid):
            ev = next((e for e in reversed(json.loads(r.events or "[]")) if e.get("type") == "run_waiting"), {})
            w = self.workflows.get(r.workflow_id) if r.workflow_id and r.workflow_id != "adhoc" else None
            out.append({"id": r.id, "workflow_id": r.workflow_id, "workflow_name": w.name if w else None, "node": ev.get("node"),
                        "label": ev.get("label"), "prompt": ev.get("prompt"), "started": r.started, "waiting_since": r.ended})
        return out

    def cancel_waiting(self, rid: str, uid: str) -> None:
        r = self.waiting_run(rid, uid)
        self._close_waiting(r, {"type": "run_cancelled", "ts": time.time(), "reason": "api"}, "cancelled", uid)

    # ---- history ----
    def history(self, wid: str, uid: str) -> list[dict]:
        if self.workflows.get_owned(wid, uid) is None: raise AppError("WORKFLOW_NOT_FOUND")
        return [{"id": r.id, "workflow_id": r.workflow_id, "input": json.loads(r.input or "null"), "events": json.loads(r.events or "[]"),
                 "final_state": json.loads(r.final_state or "null"), "status": r.status, "started": r.started, "ended": r.ended, "source": r.source or "ui", "version": r.workflow_version,
                 "metrics": None if r.duration_ms is None else {"duration_ms": r.duration_ms, "tokens_in": r.tokens_in, "tokens_out": r.tokens_out,
                                                                "tokens": (r.tokens_in or 0) + (r.tokens_out or 0), "cost_usd": r.cost_usd, "error_count": r.error_count},
                 "trace_id": r.trace_id, "trace_url": trace_url(r.trace_id)}
                for r in self.runs.list_for_workflow(wid)]

    def record(self, rid, wid, inp, events, final, status, t0, uid: str = "", checkpoint: dict | None = None, source: str = "ui",
               version: Optional[int] = None, span=None, trace_parent: Optional[dict] = None, trace_events: Optional[list] = None,
               fence: Optional[int] = None) -> dict:
        """Persist the run with its summary metrics and close its trace segment. Returns {metrics, trace_id, trace_url}.
        span: the live root span (node spans were already exported). Without one, the trace is built post-hoc from
        `trace_events` (default: all events) under `trace_parent` (the previous segment of a paused run).
        A waiting run keeps its checkpoint, which remembers the trace so the resumed segment joins it.
        fence: lease generation of a queue job; raises StaleLease (nothing written) when another worker owns the run."""
        if fence is not None and self.runs.lease_gen(rid) != fence: raise StaleLease(rid)  # before any side effect (spans, notifications)
        t1 = time.time(); metrics = summarize(events, t0, t1)  # from the full events, before capping
        trace_id = None; run_meta = {"id": rid, "workflow_id": wid, "owner": uid, "status": status, "started": t0, "ended": t1, "source": source}
        try:
            if span is not None:
                if checkpoint is not None: checkpoint = {**checkpoint, "trace": span.ref}
                trace_id = self.telemetry.end_run(span, {**run_meta, "started": span.run["started"]}, metrics)
            elif status != "waiting":
                trace_id = self.telemetry.record_run(run_meta, events if trace_events is None else trace_events, metrics, trace_parent)
        except Exception: trace_id = None  # tracing must never fail a run
        if trace_id is None and trace_parent: trace_id = trace_parent.get("trace_id")
        if self.notifier is not None and uid and status in ("waiting", "expired"):
            ev = next((e for e in reversed(events) if e.get("type") == "run_waiting"), None)
            try: self.notifier.run_event("run_waiting" if status == "waiting" else "run_expired", uid, rid, wid, ev)
            except Exception: log.exception("notification for run %s failed", rid)  # never fails a run
        if self.approvals is not None and uid:
            try:
                if status == "waiting":
                    ev = next((e for e in reversed(events) if e.get("type") == "run_waiting"), None)
                    if ev and checkpoint: self.approvals.on_waiting(rid, uid, wid, checkpoint.get("workflow") or {}, ev)
                elif status in ("cancelled", "expired", "error", "timeout"): self.approvals.close_run(rid, status)
            except Exception: log.exception("approval request for run %s failed", rid)  # never fails a run
        events = cap_run([cap_event(e) for e in events])
        final = cap_event({"state": final})["state"] if final is not None else None
        self.runs.add(Run(id=rid, workflow_id=wid or "adhoc", input=_dumps(inp), events=_dumps(events),
                          final_state=_dumps(final), status=status, started=t0, ended=t1, trace_id=trace_id, owner=uid or None, source=source, workflow_version=version,
                          checkpoint=_dumps(checkpoint) if checkpoint else None, **metrics), **({"fence": fence} if fence is not None else {}))
        if self.ledger is not None and status != "waiting":
            try: self.ledger.purge(rid)  # finished: the ledger only matters while the run can still be recovered
            except Exception: log.warning("purging the node ledger of run %s failed", rid)
        return {"metrics": {**metrics, "tokens": metrics["tokens_in"] + metrics["tokens_out"]}, "trace_id": trace_id, "trace_url": trace_url(trace_id)}

    async def _save_progress(self, rid, events, ev, plan, span) -> None:
        """Persist events so far + where to continue from if this worker dies (TASK-0020/0021): the next node(s),
        state and iteration counts (or the imported graph's serialized LangGraph checkpoint), plus the trace segment.
        Raises StaleLease when another worker claimed the run (this one must stop)."""
        cp = {"kind": "progress", **{k: ev[k] for k in RESUME_KEYS if k in ev}, "workflow": plan.workflow, "ts": time.time(),
              **({"trace": span.ref} if span else {})}
        try: await asyncio.to_thread(self.runs.save_progress, rid, _dumps(cap_run([cap_event(e) for e in events])), _dumps(cp), plan.fence)
        except StaleLease: raise
        except Exception: log.warning("saving progress of run %s failed", rid)  # recovery falls back to a restart

    # ---- execution ----
    async def execute(self, plan: RunPlan, send: Callable[[dict], Awaitable[bool]],
                      listen: Callable[[], Awaitable[str]], uid: str = "") -> str:
        """Stream events through `send` (returns False once the client is gone). `listen` resolves to
        "cancelled" or "disconnected"; a cancel can also arrive through the RunBus (reason "api").
        Returns the final status: ok | error | cancelled | timeout."""
        rid = plan.run_id or uuid.uuid4().hex[:10]; await self.bus.astart(rid, uid)  # registered so REST/other workers can cancel it
        status = None
        try:
            status = await self._execute(rid, plan, send, listen, uid)
            if status != "fenced": await self.settled(rid)
            return status
        finally:
            if status != "fenced": await asyncio.shield(self.bus.afinish(rid))  # a fenced worker leaves the new owner's entry alone

    async def settled(self, rid: str) -> None:
        """Every run segment ends here (first run, studio/Slack/Telegram resume, recovery): an API run's callback_url
        gets the result or the next pause, once (DeliveryService.for_run is idempotent)."""
        if not self.deliveries: return
        try: await asyncio.to_thread(self.deliveries().for_run, self.runs.get(rid))
        except Exception: log.exception("queueing the callback of run %s failed", rid)

    async def _execute(self, rid, plan, send, listen, uid) -> str:
        t0 = time.time(); events: list = []; final = None; status = "ok"; connected = True; bus = self.bus; checkpoint = None
        prev = plan.previous; started = prev.started if prev else t0
        try: span = self.telemetry.start_run({"id": rid, "workflow_id": plan.workflow_id, "owner": uid, "started": t0,
                                              "segment": "recovered" if plan.recovered or plan.fence and plan.attempt > 1 else "resumed"}, plan.trace_parent,
                                             links=[plan.trace_parent] if plan.trace_parent and (plan.recovered or plan.attempt > 1) else None)
        except Exception: span = None  # tracing must never fail a run
        if prev: events.extend(json.loads(prev.events or "[]"))  # resumed: one run, one event log
        q: asyncio.Queue = asyncio.Queue(); loop = asyncio.get_running_loop(); cancel = threading.Event()

        def put(x):
            try: loop.call_soon_threadsafe(q.put_nowait, x)
            except RuntimeError: pass  # loop closed after client went away

        plan.effects = Effects(rid, plan.attempt, ledger=_RunLedger(self.ledger, rid, plan.fence) if self.ledger is not None else None,
                          guard=self._guard(rid, plan.fence))

        def worker():
            g = None
            try:
                g = plan.events()
                for ev in g:
                    if cancel.is_set(): break  # cooperative cancel between steps
                    if bus.is_cancelled(rid): put(CANCEL_API); break  # cancel requested via REST / another worker
                    put(ev)
            except StaleLease:
                put(FENCED)
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
            if span is not None and ev.get("type") in ("node_finished", "error"):
                try: self.telemetry.node(span, ev)  # live span (TASK-0020)
                except Exception: pass
            try: await bus.apublish(rid, ev)
            except Exception: pass  # fan-out is best effort; the socket and history stay authoritative
            if connected: connected = await send(cap_event(ev))

        try:
            if plan.recovered: first = {"type": "run_recovered", "run_id": rid, "ts": t0, "node": plan.resume["node"], "nodes": resume_nodes(plan.resume),
                                        "attempt": plan.attempt}
            elif prev: first = {"type": "run_resumed", "run_id": rid, "ts": t0, "node": plan.resume["node"], "response": plan.resume["value"],
                                **({"by": plan.resumed_by} if plan.resumed_by else {})}
            else: first = {"type": "run_started", "run_id": rid, "ts": t0}
            await emit(first)
            if plan.checkpointing: await self._save_progress(rid, events, plan.resume or {}, plan, span)  # this segment's trace, before any node
            threading.Thread(target=worker, daemon=True).start()
            listener = asyncio.create_task(listen()); deadline = t0 + config.run_timeout(); ended = None
            while True:
                get = asyncio.ensure_future(q.get())
                done, _ = await asyncio.wait({get, listener}, timeout=max(0.0, deadline - time.time()), return_when=asyncio.FIRST_COMPLETED)
                if get in done:
                    ev = get.result()
                    if ev is None: break
                    if ev is CANCEL_API: ended = "api"; cancel.set(); break
                    if ev is FENCED: ended = "fenced"; cancel.set(); break
                    if ev.get("type") == "_checkpoint":  # engine progress marker: never sent or stored as an event
                        if plan.checkpointing:
                            try: await self._save_progress(rid, events, ev, plan, span)
                            except StaleLease: ended = "fenced"; cancel.set(); break
                        continue
                    if ev.get("type", "").startswith("_"): continue  # other internal markers (e.g. sandbox `_restart`)
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
            if ended == "fenced": return self._fenced(rid, span, plan, uid, t0)
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
            try: await asyncio.shield(asyncio.to_thread(self.record, rid, plan.workflow_id, plan.input, events, final, status, started, uid, None,
                                                        plan.source, plan.version, span, fence=plan.fence))
            except StaleLease: self._fenced(rid, span, plan, uid, t0)
            raise
        try: summary = await asyncio.to_thread(self.record, rid, plan.workflow_id, plan.input, events, final, status, started, uid, checkpoint,
                                               plan.source, plan.version, span, fence=plan.fence)
        except StaleLease: return self._fenced(rid, span, plan, uid, t0)
        if connected: await send({"type": "run_summary", "run_id": rid, "status": status, "ts": time.time(), **summary})  # not stored as an event
        return status

    def _guard(self, rid: str, fence: Optional[int]):
        """Fencing check before every side-effect node of a queue job (TASK-0021)."""
        if fence is None: return None
        def check():
            if self.runs.lease_gen(rid) != fence: raise StaleLease(rid)
        return check

    def _fenced(self, rid, span, plan, uid, t0) -> str:
        """Another worker claimed this run: stop without writing anything; close our trace segment as cancelled."""
        log.warning("run %s: lease generation %s is stale, this worker stops (another worker owns the run)", rid, plan.fence)
        try: self.telemetry.end_run(span, {"id": rid, "status": "cancelled", "started": t0, "ended": time.time(), "source": plan.source},
                                    {"error_count": 0, "tokens_in": 0, "tokens_out": 0, "cost_usd": None, "duration_ms": 0}, observe=False)
        except Exception: pass
        return "fenced"
