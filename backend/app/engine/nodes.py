"""Node executors: build the LangGraph node function for each node type."""
from __future__ import annotations
from typing import Any, Callable, Dict, Optional
import httpx
from .effects import Effects, call_tool
from .errors import Interrupt
from .llm import LLMError, TokenBuffer, call_llm
from .ports import Ports
from .templating import render, render_args
from .tools import TOOLS
from .usage import UsageSink


Resolver = Callable[[str], Dict[str, Any]]


def token_stream(nid: str) -> Optional[TokenBuffer]:
    """Live LLM text for the run stream (TASK-0030): LangGraph `custom` stream mode, None outside a streamed run."""
    try: from langgraph.config import get_stream_writer; write = get_stream_writer()
    except Exception: return None
    return TokenBuffer(lambda delta: write({"node": nid, "delta": delta}))


def node_fn(node: Dict[str, Any], resolve: Optional[Resolver] = None, usage: Optional[UsageSink] = None,
            resume: Optional[Dict[str, Any]] = None, effects: Optional[Effects] = None, ports: Optional[Ports] = None):
    """resolve(credential_id) -> decrypted credential; bound to the run's user by the service layer.
    usage(node_id, record): optional sink for LLM token usage (TASK-0010).
    effects: idempotency keys for side effects (TASK-0021): HTTP Tool nodes send `Idempotency-Key`.
    ports: user-bound services (knowledge base search, MCP calls; TASK-0012/0013)."""
    ports = ports or Ports()
    t, d = node["type"], node.get("data", {})
    if t == "llm":
        def fn(state):
            cred = None
            if d.get("credential_id"):
                if resolve is None: raise LLMError("Node uses a credential but no resolver is available")
                cred = resolve(d["credential_id"])
            report = (lambda u: usage(node["id"], u)) if usage else None
            tokens = token_stream(node["id"])
            try: return {d["output_field"]: call_llm(render(d.get("prompt", ""), state), d.get("model", "gpt-4o-mini"), cred, report, tokens)}
            finally:
                if tokens: tokens.flush()
    elif t == "human":
        def fn(state):
            # resume = {"node", "value"} for the node the run paused at; consumed once so a loop back here pauses again
            if resume is not None and resume.get("node") == node["id"] and "value" in resume:
                return {d["output_field"]: resume.pop("value")}
            raise Interrupt(node["id"], render(d.get("prompt", ""), state))
    elif t == "tool":
        def fn(state):
            if d.get("mode") == "http":
                body = render(d.get("body", ""), state)
                r = httpx.request(d.get("method", "GET"), render(d["url"], state),
                                  content=body.encode() if body else None,
                                  headers={"Content-Type": "application/json", **(effects.headers(node["id"]) if effects else {})}, timeout=30)
                try: res = r.json()
                except Exception: res = r.text
            else:
                res = call_tool(TOOLS[d["function"]], state, effects.key(node["id"]) if effects else None)
            return {d["output_field"]: res}
    elif t == "retriever":
        def fn(state):
            if ports.retrieve is None: raise RuntimeError("Retriever nodes need a knowledge base service")
            query = render(d.get("query", ""), state)
            return {d["output_field"]: ports.retrieve(d["knowledge_base_id"], query, int(d.get("top_k") or 4))}
    elif t == "mcp":
        def fn(state):
            if ports.mcp_call is None: raise RuntimeError("MCP nodes need the MCP service")
            return {d["output_field"]: ports.mcp_call(d["server_id"], d["tool"], render_args(d.get("arguments") or {}, state))}
    else:  # start, condition, end, join, subgraph entry/exit -> passthrough
        def fn(state):
            return {}
    return fn
