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


@dataclass
class RunPlan:
    workflow_id: Optional[str]
    workflow: dict
    input: dict
    resolve: Optional[Callable[[str], dict]] = None  # credential lookup bound to the run's user

    @property
    def imported(self) -> bool:
        return (self.workflow.get("source") or {}).get("kind") == "langgraph_import"

    def events(self) -> Iterator[dict]:
        if self.imported: return repo_import.run_imported(self.workflow, dict(self.input))
        return run_stream(self.workflow, self.input, self.resolve)


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


def _dumps(x) -> str: return json.dumps(x, ensure_ascii=False, default=str)


class RunService:
    def __init__(self, workflows: WorkflowRepository, runs: RunRepository, credentials=None):
        """credentials: CredentialService (optional; without it, nodes with credential_id fail clearly)."""
        self.workflows, self.runs, self.credentials = workflows, runs, credentials

    # ---- planning / validation of the client request ----
    def plan(self, uid: str, req) -> RunPlan:
        if not isinstance(req, dict): raise AppError("RUN_REQUEST_INVALID")
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

    # ---- history ----
    def history(self, wid: str, uid: str) -> list[dict]:
        if self.workflows.get_owned(wid, uid) is None: raise AppError("WORKFLOW_NOT_FOUND")
        return [{"id": r.id, "workflow_id": r.workflow_id, "input": json.loads(r.input or "null"), "events": json.loads(r.events or "[]"),
                 "final_state": json.loads(r.final_state or "null"), "status": r.status, "started": r.started, "ended": r.ended}
                for r in self.runs.list_for_workflow(wid)]

    def record(self, rid, wid, inp, events, final, status, t0) -> None:
        events = cap_run([cap_event(e) for e in events])
        final = cap_event({"state": final})["state"] if final is not None else None
        self.runs.add(Run(id=rid, workflow_id=wid or "adhoc", input=_dumps(inp), events=_dumps(events),
                          final_state=_dumps(final), status=status, started=t0, ended=time.time()))

    # ---- execution ----
    async def execute(self, plan: RunPlan, send: Callable[[dict], Awaitable[bool]],
                      listen: Callable[[], Awaitable[str]]) -> str:
        """Stream events through `send` (returns False once the client is gone). `listen` resolves to
        "cancelled" or "disconnected". Returns the final status: ok | error | cancelled | timeout."""
        rid = uuid.uuid4().hex[:10]; t0 = time.time(); events: list = []; final = None; status = "ok"
        q: asyncio.Queue = asyncio.Queue(); loop = asyncio.get_running_loop(); cancel = threading.Event()
        connected = True

        def put(x):
            try: loop.call_soon_threadsafe(q.put_nowait, x)
            except RuntimeError: pass  # loop closed after client went away

        def worker():
            g = None
            try:
                g = plan.events()
                for ev in g:
                    if cancel.is_set(): break  # cooperative cancel between steps
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
            if connected: connected = await send(cap_event(ev))

        await emit({"type": "run_started", "run_id": rid, "ts": t0})
        threading.Thread(target=worker, daemon=True).start()
        listener = asyncio.create_task(listen()); deadline = t0 + config.run_timeout(); ended = None
        while True:
            get = asyncio.ensure_future(q.get())
            done, _ = await asyncio.wait({get, listener}, timeout=max(0.0, deadline - time.time()), return_when=asyncio.FIRST_COMPLETED)
            if get in done:
                ev = get.result()
                if ev is None: break
                ev = _normalise(ev); ev["ts"] = time.time()
                if ev["type"] == "run_finished": final = ev.get("state")
                if ev["type"] == "error": status = "error"
                await emit(ev); continue
            get.cancel()
            if listener in done:
                ended = listener.result(); connected = connected and ended == "cancelled"
            else:
                ended = "timeout"
            cancel.set(); break
        if not listener.done(): listener.cancel()
        if ended in ("cancelled", "disconnected"):
            status = "cancelled"
            await emit({"type": "run_cancelled", "ts": time.time(), "reason": "client" if ended == "cancelled" else "disconnect"})
        elif ended == "timeout":
            status = "timeout"
            await emit(error_event(AppError("RUN_TIMEOUT", seconds=f"{config.run_timeout():g}").to_dict(), status="timeout", ts=time.time()))
        await asyncio.to_thread(self.record, rid, plan.workflow_id, plan.input, events, final, status, t0)
        return status
