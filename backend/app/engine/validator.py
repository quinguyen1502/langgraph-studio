"""Static workflow validation: returns a list of human-readable errors (empty = valid)."""
from __future__ import annotations
import json
from typing import Any, Dict, List
from .node_policy import errors as policy_errors
from .templating import VAR_RE
from .reducers import field_errors, reducer_of
from .tools import TOOLS

TYPES = ("start", "llm", "tool", "condition", "end", "human", "join", "subgraph", "subgraph_exit", "retriever", "mcp")
WRITERS = ("llm", "tool", "human", "retriever", "mcp")


def validate(wf: Dict[str, Any]) -> List[str]:
    errs: List[str] = []
    nodes = [n for n in wf.get("nodes", []) if isinstance(n, dict)]
    edges = [e for e in wf.get("edges", []) if isinstance(e, dict)]
    if any(not n.get("id") for n in nodes): return ["Every node needs an id"]
    if any(not e.get("source") or not e.get("target") for e in edges): return ["Every edge needs a source and a target"]
    for kind, items in (("node", nodes), ("edge", edges)):
        seen_ids, dup = set(), set()
        for x in items:
            if x.get("id") in seen_ids: dup.add(str(x.get("id")))
            seen_ids.add(x.get("id"))
        if dup: errs.append(f"Duplicate {kind} id: {', '.join(sorted(dup))}")
    ids = {n["id"] for n in nodes}
    types = {n["id"]: n.get("type") for n in nodes}
    starts = [n for n in nodes if n.get("type") == "start"]
    ends = [n for n in nodes if n.get("type") == "end"]
    if not starts: errs.append("Exactly one Start node is required (none found)")
    elif len(starts) > 1: errs.append(f"Only one Start node is allowed (found {len(starts)}: {', '.join(n['id'] for n in starts)})")
    if not ends: errs.append("At least one End node is required")
    schema = [f for f in wf.get("state", []) if isinstance(f, dict) and f.get("name")]
    fields = {f["name"] for f in schema}
    for f in schema: errs += field_errors(f)
    for e in edges:
        missing = [x for x in (e["source"], e["target"]) if x not in ids]
        if missing:
            errs.append(f"Edge {e.get('id')} points to a missing node: {', '.join(missing)}")
        elif e["source"] == e["target"] and types.get(e["source"]) != "condition":
            errs.append(f"Node {e['source']}: cannot connect to itself (only a Condition may create a loop)")
    edges = [e for e in edges if e["source"] in ids and e["target"] in ids]
    out = {i: [e for e in edges if e["source"] == i] for i in ids}
    for n in nodes:
        t, d, nid = n.get("type"), n.get("data", {}), n["id"]
        if t not in TYPES:
            errs.append(f"Node {nid}: invalid type '{t}'")
        if t != "end" and not out.get(nid):
            errs.append(f"Node {nid} ({d.get('label', t)}) has no outgoing edge")
        if t == "end" and out.get(nid):
            errs.append(f"End node {nid} must not have outgoing edges")
        if t == "start" and any(e["target"] == nid for e in edges):
            errs.append("Start must not have incoming edges")
        if t in WRITERS:
            of = d.get("output_field")
            if not of: errs.append(f"Node {nid}: output_field is missing")
            elif fields and of not in fields: errs.append(f"Node {nid}: output_field '{of}' is not in the state")
        if t == "tool":
            if d.get("mode", "function") == "function" and d.get("function") not in TOOLS:
                errs.append(f"Node {nid}: function '{d.get('function')}' is not registered")
            if d.get("mode") == "http" and not d.get("url"):
                errs.append(f"Node {nid}: URL is missing")
        if t == "join":
            inc = [e for e in edges if e["target"] == nid]
            if len(inc) < 2: errs.append(f"Join node {nid}: needs at least two incoming edges (the branches it waits for)")
            if any(types.get(e["source"]) == "condition" for e in inc):
                errs.append(f"Join node {nid}: a Condition cannot feed a Join directly (the Join would wait for a branch that may never run)")
        if t == "retriever":
            if not d.get("knowledge_base_id"): errs.append(f"Retriever node {nid}: choose a knowledge base")
            k = d.get("top_k", 4)
            if not isinstance(k, int) or isinstance(k, bool) or not 1 <= k <= 20: errs.append(f"Retriever node {nid}: top_k must be 1-20")
            for v in VAR_RE.findall(d.get("query", "")):
                if fields and v not in fields: errs.append(f"Node {nid}: variable state.{v} is not in the state")
        if t == "mcp":
            if not d.get("server_id"): errs.append(f"MCP node {nid}: choose a server")
            if not d.get("tool"): errs.append(f"MCP node {nid}: choose a tool")
            if not isinstance(d.get("arguments", {}), dict): errs.append(f"MCP node {nid}: arguments must be an object")
            for v in VAR_RE.findall(json.dumps(d.get("arguments") or {})):
                if fields and v not in fields: errs.append(f"Node {nid}: variable state.{v} is not in the state")
        if t == "subgraph" and not d.get("workflow_id"):
            errs.append(f"Subgraph node {nid}: choose a workflow")
        if t == "condition":
            if not d.get("field"): errs.append(f"Node {nid}: Condition field is missing")
            labels = [e.get("label") for e in out.get(nid, [])]
            if any(not l for l in labels): errs.append(f"Node {nid}: every outgoing Condition edge needs a label")
            if len(set(labels)) != len(labels): errs.append(f"Node {nid}: duplicate labels")
        if t == "llm":
            for v in VAR_RE.findall(d.get("prompt", "")):
                if fields and v not in fields: errs.append(f"Node {nid}: variable state.{v} is not in the state")
        errs += policy_errors(nid, d, fields)
    # parallel branches (several outgoing edges, no Condition) that write the same field need a reducer
    red = {f["name"]: reducer_of(f) for f in schema}
    for n in nodes:
        if n.get("type") == "condition" or len(out.get(n["id"], [])) < 2: continue
        writes: Dict[str, List[str]] = {}
        for e in out[n["id"]]:
            tgt = next((x for x in nodes if x["id"] == e["target"]), None)
            of = (tgt or {}).get("data", {}).get("output_field") if (tgt or {}).get("type") in WRITERS else None
            if of: writes.setdefault(of, []).append(tgt["id"])
        for of, who in writes.items():
            if len(who) > 1 and red.get(of, "replace") == "replace":
                errs.append(f"Parallel nodes {', '.join(who)} all write state.{of}: give the field a reducer (append, merge or add) or use different fields")
    # cycles must pass through a Condition node (otherwise the loop can never exit)
    plain = {i: [e["target"] for e in out.get(i, []) if types.get(e["target"]) != "condition" and e["target"] != i] for i in ids if types.get(i) != "condition"}
    state_: Dict[str, int] = {}
    def dfs(u, path):
        state_[u] = 1; path.append(u)
        for v in plain.get(u, []):
            if state_.get(v) == 1:
                cyc = path[path.index(v):] + [v]
                errs.append(f"Loop without a Condition: {' → '.join(cyc)}")
                return True
            elif not state_.get(v) and dfs(v, path): return True
        path.pop(); state_[u] = 2; return False
    for i in sorted(plain):
        if not state_.get(i) and dfs(i, []): break
    # reachability
    if len(starts) == 1:
        seen, stack = set(), [starts[0]["id"]]
        while stack:
            x = stack.pop()
            if x in seen: continue
            seen.add(x); stack += [e["target"] for e in out.get(x, [])]
        for n in nodes:
            if n["id"] not in seen: errs.append(f"Node {n['id']} is not reachable from Start")
    return errs
