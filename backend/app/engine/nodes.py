"""Node executors: build the LangGraph node function for each node type."""
from __future__ import annotations
from typing import Any, Callable, Dict, Optional
import httpx
from .llm import LLMError, call_llm
from .templating import render
from .tools import TOOLS
from .usage import UsageSink


Resolver = Callable[[str], Dict[str, Any]]


def node_fn(node: Dict[str, Any], resolve: Optional[Resolver] = None, usage: Optional[UsageSink] = None):
    """resolve(credential_id) -> decrypted credential; bound to the run's user by the service layer.
    usage(node_id, record): optional sink for LLM token usage (TASK-0010)."""
    t, d = node["type"], node.get("data", {})
    if t == "llm":
        def fn(state):
            cred = None
            if d.get("credential_id"):
                if resolve is None: raise LLMError("Node uses a credential but no resolver is available")
                cred = resolve(d["credential_id"])
            report = (lambda u: usage(node["id"], u)) if usage else None
            return {d["output_field"]: call_llm(render(d.get("prompt", ""), state), d.get("model", "gpt-4o-mini"), cred, report)}
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
