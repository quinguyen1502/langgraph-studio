"""Compile workflow JSON {nodes, edges, state} into a LangGraph StateGraph."""
from __future__ import annotations
from typing import Annotated, Any, Dict, Optional, TypedDict
from langgraph.graph import StateGraph, START, END
from .errors import ValidationError
from .nodes import node_fn
from .reducers import fn_of
from .validator import validate

TYPE_MAP = {"string": str, "number": float, "integer": int, "boolean": bool, "object": dict, "list": list}


def compile_workflow(wf: Dict[str, Any], resolve=None, usage=None, entry=None, resume=None, effects=None, checkpointer=None, ports=None):
    """entry: start the graph at this node (or these nodes, run in parallel) instead of Start (resuming a paused or
    recovered run, TASK-0006/0021). effects: idempotency keys + node-result ledger (TASK-0021).
    checkpointer: LangGraph saver, used by the runtime to observe superstep checkpoints."""
    entries = set([entry] if isinstance(entry, str) else (entry or []))
    errs = validate(wf)
    if errs: raise ValidationError(errs)
    def annotation(f):
        typ = TYPE_MAP.get(f.get("type", "string"), str); fn = fn_of(f)
        return Annotated[typ, fn] if fn else Optional[typ]  # reducer fields: LangGraph combines parallel writes (TASK-0011)
    ann = {f["name"]: annotation(f) for f in wf.get("state", [])}
    State = TypedDict("State", ann, total=False)  # type: ignore
    g = StateGraph(State)
    nodes = {n["id"]: n for n in wf["nodes"]}
    joins = {nid for nid, n in nodes.items() if n["type"] == "join"}
    for nid, n in nodes.items():
        fn = node_fn(n, resolve, usage, resume, effects, ports)
        g.add_node(nid, effects.wrap(n, fn) if effects else fn)
    for nid, n in nodes.items():
        out = [e for e in wf["edges"] if e["source"] == nid]
        if nid in entries or (not entries and n["type"] == "start"):
            g.add_edge(START, nid)
        if n["type"] == "end":
            g.add_edge(nid, END)
        elif n["type"] == "condition":
            field = n["data"]["field"]
            mapping = {e["label"]: e["target"] for e in out}
            default = n["data"].get("default") or ("default" if "default" in mapping else None)
            label = n["data"].get("label") or nid
            def router(state, field=field, mapping=mapping, default=default, nid=nid, label=label):
                raw = state.get(field)
                v = ("" if raw is None else str(raw).lower() if isinstance(raw, bool) else str(raw)).strip()
                if v in mapping: return v
                for k in mapping:  # case-insensitive / contains fallback
                    if k.lower() == v.lower() or k.lower() in v.lower(): return k
                if default and default in mapping: return default
                raise ValueError(f"Condition '{label}' ({nid}): value {field}='{v[:100]}' matches no label {list(mapping)} and there is no default")
            g.add_conditional_edges(nid, router, mapping)
        else:
            for e in out:
                if e["target"] not in joins: g.add_edge(nid, e["target"])  # several edges = parallel branches (TASK-0011)
    for j in joins:  # fan-in: the Join runs once, after every incoming branch finished
        if j in entries: continue
        g.add_edge([e["source"] for e in wf["edges"] if e["target"] == j], j)
    return g.compile(checkpointer=checkpointer)
