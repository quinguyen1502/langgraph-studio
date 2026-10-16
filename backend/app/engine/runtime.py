"""Runtime: stream a compiled workflow as trace events (node_started / node_finished / error / run_finished)."""
from __future__ import annotations
import json, time
from typing import Any, Dict, List
from .compiler import compile_workflow
from .errors import ValidationError
from .limits import safe_error
from .usage import merge as merge_usage
from ..core.config import recursion_limit

TRACE_CAP = 16_000  # max JSON chars per traced payload (input/delta) in an event


def cap_payload(obj: Any, limit: int = TRACE_CAP) -> Any:
    """Return obj unchanged if its JSON is small, else a truncated preview marker."""
    try:
        txt = json.dumps(obj, ensure_ascii=False, default=str)
    except Exception:
        txt = str(obj)
    if len(txt) <= limit: return obj
    return {"_truncated": True, "size": len(txt), "preview": txt[:limit]}


PY_TYPES = {"number": (int, float), "integer": (int,), "boolean": (bool,), "list": (list,), "object": (dict,), "string": (str,)}


def check_input(wf: Dict[str, Any], inputs: Any) -> List[str]:
    """Run input must be a JSON object whose known fields match the state schema types."""
    if not isinstance(inputs, dict): return ["Input must be a JSON object, e.g. {\"message\": \"hi\"}"]
    errs = []
    for f in wf.get("state", []) or []:
        name, typ = f.get("name"), f.get("type", "string")
        if name in inputs and inputs[name] is not None and typ in PY_TYPES:
            v = inputs[name]; ok = isinstance(v, PY_TYPES[typ]) and not (typ in ("number", "integer") and isinstance(v, bool))
            if not ok: errs.append(f"Input '{name}' must be of type {typ} (got {type(v).__name__})")
    return errs


def run_stream(wf: Dict[str, Any], inputs: Dict[str, Any], resolve=None):
    """Yield per-node events: started / finished(duration, input=state before, delta=output) / error. Sync generator."""
    if (bad := check_input(wf, inputs)): raise ValidationError(bad)
    usage: Dict[str, Dict[str, Any]] = {}  # node id -> usage since its last node_finished (TASK-0010)
    app = compile_workflow(wf, resolve, lambda nid, u: usage.__setitem__(nid, merge_usage(usage.get(nid), u)))
    nodes = {n["id"]: n for n in wf["nodes"]}
    state = dict(inputs); counts: Dict[str, int] = {}

    def meta(nid):
        return {"node": nid, "label": nodes[nid]["data"].get("label"), "node_type": nodes[nid]["type"]}

    def started(nid):
        counts[nid] = counts.get(nid, 0) + 1
        return {"type": "node_started", **meta(nid), "iteration": counts[nid]}

    start_id = next(n["id"] for n in wf["nodes"] if n["type"] == "start")
    yield started(start_id)
    t0 = time.perf_counter(); pending = [start_id]
    try:
        for chunk in app.stream(inputs, {"recursion_limit": recursion_limit()}, stream_mode="updates"):
            before = dict(state)
            for nid, delta in chunk.items():
                delta = delta or {}
                state.update(delta)
                yield {"type": "node_finished", **meta(nid), "iteration": counts.get(nid, 1),
                       "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
                       "input": cap_payload(before), "delta": cap_payload(delta),
                       **({"usage": usage.pop(nid)} if nid in usage else {})}
            # predict next node(s) to mark as started; keep a Condition as "current" so routing errors name it
            last = list(chunk)[-1]
            nxt = _next_nodes(wf, last, state)
            pending = nxt or ([last] if nodes[last]["type"] == "condition" else [])
            t0 = time.perf_counter()
            for n2 in nxt:
                yield started(n2)
    except Exception as e:  # attribute runtime failures to the node that was running
        nid = pending[-1] if pending else None
        yield {"type": "error", **(meta(nid) if nid in nodes else {}), "iteration": counts.get(nid, 1) if nid else None,
               "duration_ms": round((time.perf_counter() - t0) * 1000, 2), "input": cap_payload(dict(state)),
               "code": getattr(e, "code", "NODE_FAILED"), "errors": [safe_error(e)]}
        return
    yield {"type": "run_finished", "state": state}


def _next_nodes(wf, nid, state):
    n = next(x for x in wf["nodes"] if x["id"] == nid)
    out = [e for e in wf["edges"] if e["source"] == nid]
    if n["type"] == "end": return []
    if n["type"] == "condition":
        v = str(state.get(n["data"]["field"], "")).strip().lower()
        for e in out:
            if e["label"].lower() == v or e["label"].lower() in v: return [e["target"]]
        d = [e for e in out if e["label"] == (n["data"].get("default") or "default")]
        return [d[0]["target"]] if d else []
    return [e["target"] for e in out]
