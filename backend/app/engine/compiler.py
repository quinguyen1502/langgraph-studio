"""Compile workflow JSON {nodes, edges, state} into a LangGraph StateGraph."""
from __future__ import annotations
from typing import Any, Dict, Optional, TypedDict
from langgraph.graph import StateGraph, START, END
from .errors import ValidationError
from .nodes import node_fn
from .validator import validate

TYPE_MAP = {"string": str, "number": float, "integer": int, "boolean": bool, "object": dict, "list": list}


def compile_workflow(wf: Dict[str, Any], resolve=None, usage=None):
    errs = validate(wf)
    if errs: raise ValidationError(errs)
    ann = {f["name"]: Optional[TYPE_MAP.get(f.get("type", "string"), str)] for f in wf.get("state", [])}
    State = TypedDict("State", ann, total=False)  # type: ignore
    g = StateGraph(State)
    nodes = {n["id"]: n for n in wf["nodes"]}
    for nid, n in nodes.items():
        g.add_node(nid, node_fn(n, resolve, usage))
    for nid, n in nodes.items():
        out = [e for e in wf["edges"] if e["source"] == nid]
        if n["type"] == "start":
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
                g.add_edge(nid, e["target"])
    return g.compile()
