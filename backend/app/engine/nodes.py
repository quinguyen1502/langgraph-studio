"""Node executors: build the LangGraph node function for each node type."""
from __future__ import annotations
from typing import Any, Dict
import httpx
from .llm import call_llm
from .templating import render
from .tools import TOOLS


def node_fn(node: Dict[str, Any]):
    t, d = node["type"], node.get("data", {})
    if t == "llm":
        def fn(state):
            return {d["output_field"]: call_llm(render(d.get("prompt", ""), state), d.get("model", "gpt-4o-mini"))}
    elif t == "tool":
        def fn(state):
            if d.get("mode") == "http":
                body = render(d.get("body", ""), state)
                r = httpx.request(d.get("method", "GET"), render(d["url"], state),
                                  content=body.encode() if body else None,
                                  headers={"Content-Type": "application/json"}, timeout=30)
                try: res = r.json()
                except Exception: res = r.text
            else:
                res = TOOLS[d["function"]](state)
            return {d["output_field"]: res}
    else:  # start, condition, end -> passthrough
        def fn(state):
            return {}
    return fn
