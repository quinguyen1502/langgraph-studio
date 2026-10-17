"""Runtime: stream a compiled workflow as trace events (node_started / node_finished / error / run_finished)."""
from __future__ import annotations
import json, time
from typing import Any, Dict, List, Optional
from langgraph.checkpoint.memory import InMemorySaver
from .compiler import compile_workflow
from .effects import Effects
from .errors import Interrupt, ValidationError
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


def run_stream(wf: Dict[str, Any], inputs: Dict[str, Any], resolve=None, resume: Dict[str, Any] | None = None,
               effects: Optional[Effects] = None):
    """Yield per-node events: started / finished(duration, input=state before, delta=output) / error. Sync generator.
    A Human node without a response yields `run_waiting` {node, prompt, checkpoint} and stops.
    resume = {"node" | "nodes", "state", "counts"?, "value"?} continues at that node (or those parallel nodes) with the
    saved state: with "value" a paused Human node gets its response (TASK-0006); without it the run continues from a
    progress checkpoint (recovery of queue jobs, TASK-0020).
    Progress checkpoints come from LangGraph itself (TASK-0021): the graph is compiled with an in-memory saver and its
    superstep checkpoints are observed (`stream_mode="checkpoints"`), so a step with several parallel nodes (fan-out)
    is resumable too. Each yields `_checkpoint` {node, nodes, state, counts}; callers must not forward it to clients.
    effects: idempotency keys + node-result ledger + fencing guard for side-effect nodes (TASK-0021)."""
    if resume is None and (bad := check_input(wf, inputs)): raise ValidationError(bad)
    usage: Dict[str, Dict[str, Any]] = {}  # node id -> usage since its last node_finished (TASK-0010)
    held = {"node": resume["node"], "value": resume["value"]} if resume and "value" in resume else None
    counts: Dict[str, int] = {k: int(v) for k, v in ((resume or {}).get("counts") or {}).items()}
    if effects is not None: effects.counts = counts  # node iterations feed the idempotency keys
    app = compile_workflow(wf, resolve, lambda nid, u: usage.__setitem__(nid, merge_usage(usage.get(nid), u)),
                           entry=resume_nodes(resume) if resume else None, resume=held, effects=effects, checkpointer=InMemorySaver())
    nodes = {n["id"]: n for n in wf["nodes"]}
    if resume: inputs = dict(resume.get("state") or {})
    state = dict(inputs); cp_state, cp_counts = dict(state), dict(counts); first = True

    def meta(nid):
        return {"node": nid, "label": nodes[nid]["data"].get("label"), "node_type": nodes[nid]["type"]}

    def started(nid):
        counts[nid] = counts.get(nid, 0) + 1
        return {"type": "node_started", **meta(nid), "iteration": counts[nid]}

    t0 = time.perf_counter(); pending: List[str] = []
    cfg = {"recursion_limit": recursion_limit(), "configurable": {"thread_id": "run"}}
    try:
        for mode, chunk in app.stream(inputs, cfg, stream_mode=["updates", "checkpoints"]):
            if mode == "checkpoints":  # superstep boundary: the nodes that run next, all inputs settled
                nxt = [n for n in (chunk.get("next") or []) if n in nodes]
                if not nxt: continue
                cp_state, cp_counts = dict(state), dict(counts)
                if not first and any(nodes[n]["type"] not in ("start", "end") for n in nxt):
                    yield {"type": "_checkpoint", "node": nxt[0], "nodes": nxt, "state": dict(state), "counts": dict(counts)}
                first = False; pending = nxt; t0 = time.perf_counter()
                for n2 in nxt: yield started(n2)
                continue
            before = dict(state)
            for nid, delta in chunk.items():
                if nid not in nodes: continue
                delta = delta or {}
                state.update(delta)
                reused = effects is not None and nid in effects.reused
                if reused: effects.reused.discard(nid)
                yield {"type": "node_finished", **meta(nid), "iteration": counts.get(nid, 1),
                       "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
                       "input": cap_payload(before), "delta": cap_payload(delta),
                       **({"usage": usage.pop(nid)} if nid in usage else {}), **({"reused": True} if reused else {})}
    except Interrupt as i:  # a Human node is waiting: hand back a checkpoint instead of an error
        # parallel siblings of the Human node resume with it (their results come from the ledger when recorded)
        yield {"type": "run_waiting", **meta(i.node), "prompt": i.prompt, "state": cap_payload(dict(state)),
               "checkpoint": {"node": i.node, "nodes": pending or [i.node], "state": cp_state, "counts": cp_counts}}
        return
    except Exception as e:  # attribute runtime failures to the node that was running
        if getattr(e, "fenced", False): raise  # this worker lost the run: the service layer stops without writing
        nid = pending[-1] if pending else None
        yield {"type": "error", **(meta(nid) if nid in nodes else {}), "iteration": counts.get(nid, 1) if nid else None,
               "duration_ms": round((time.perf_counter() - t0) * 1000, 2), "input": cap_payload(dict(state)),
               "code": getattr(e, "code", "NODE_FAILED"), "errors": [safe_error(e)]}
        return
    yield {"type": "run_finished", "state": state}


def resume_nodes(resume: Dict[str, Any]) -> List[str]:
    """Entry nodes of a resume/recovery checkpoint (older checkpoints only have "node")."""
    return list(resume.get("nodes") or [resume["node"]])
