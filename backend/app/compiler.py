"""Compile workflow JSON {nodes, edges, state} into a LangGraph StateGraph."""
from __future__ import annotations
import json, operator, os, re, time
from typing import Any, Callable, Dict, List, Optional, TypedDict
import httpx
from .limits import safe_error
from langgraph.graph import StateGraph, START, END

TYPE_MAP = {"string": str, "number": float, "integer": int, "boolean": bool, "object": dict, "list": list}
VAR_RE = re.compile(r"\{\{\s*state\.([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


class ValidationError(Exception):
    def __init__(self, errors: List[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


def render(template: str, state: Dict[str, Any]) -> str:
    def rep(m):
        v = state.get(m.group(1), "")
        return v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    return VAR_RE.sub(rep, template or "")


# ---------------- Tool registry ----------------
TOOLS: Dict[str, Callable[[Dict[str, Any]], Any]] = {}

def register_tool(name: str):
    def deco(fn):
        TOOLS[name] = fn
        return fn
    return deco

ORDERS = {"A100": "Đã giao hàng (delivered) ngày 2026-10-10",
          "B200": "Đang vận chuyển (in transit), dự kiến 2026-10-18",
          "C300": "Đang xử lý (processing)"}

@register_tool("lookup_order")
def lookup_order(state: Dict[str, Any]) -> str:
    """Example function: find an order id (e.g. A100) in state.message and return status."""
    m = re.search(r"\b([A-Z]\d{3})\b", str(state.get("message", "")).upper())
    if not m:
        return "Không tìm thấy mã đơn hàng trong tin nhắn."
    oid = m.group(1)
    return f"Đơn {oid}: {ORDERS.get(oid, 'không tồn tại trong hệ thống')}"


# ---------------- LLM ----------------
if os.environ.get("STUDIO_ENABLE_DEMO_TOOLS") == "1":
    @register_tool("sleep_demo")
    def sleep_demo(state: Dict[str, Any]) -> str:
        """Demo/testing only (STUDIO_ENABLE_DEMO_TOOLS=1): sleeps 1.5 s, to exercise cancel/timeout."""
        time.sleep(1.5); return "slept 1.5s"


def mock_llm(prompt: str, model: str) -> str:
    """Deterministic offline mock. Recognises classification prompts."""
    p = prompt.lower()
    if "classify" in p or "phân loại" in p:
        msg = p.split("message:")[-1] if "message:" in p else p
        if any(k in msg for k in ["order", "đơn", "giao hàng", "ship", "a100", "b200", "c300"]):
            return "order_status"
        if any(k in msg for k in ["refund", "hoàn tiền", "return"]):
            return "refund"
        return "general"
    tail = prompt.strip().splitlines()[-1] if prompt.strip() else ""
    return f"[mock:{model}] Trả lời: {tail[:200]}"


def call_llm(prompt: str, model: str) -> str:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return mock_llm(prompt, model)
    base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    r = httpx.post(f"{base}/chat/completions", headers={"Authorization": f"Bearer {key}"},
                   json={"model": model or "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}]},
                   timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


# ---------------- Validation ----------------
def validate(wf: Dict[str, Any]) -> List[str]:
    errs: List[str] = []
    nodes = [n for n in wf.get("nodes", []) if isinstance(n, dict)]
    edges = [e for e in wf.get("edges", []) if isinstance(e, dict)]
    if any(not n.get("id") for n in nodes): return ["Mọi node cần có id"]
    if any(not e.get("source") or not e.get("target") for e in edges): return ["Mọi edge cần có source và target"]
    for kind, items in (("node", nodes), ("edge", edges)):
        seen_ids, dup = set(), set()
        for x in items:
            if x.get("id") in seen_ids: dup.add(str(x.get("id")))
            seen_ids.add(x.get("id"))
        if dup: errs.append(f"Trùng id {kind}: {', '.join(sorted(dup))}")
    ids = {n["id"] for n in nodes}
    types = {n["id"]: n.get("type") for n in nodes}
    starts = [n for n in nodes if n.get("type") == "start"]
    ends = [n for n in nodes if n.get("type") == "end"]
    if not starts: errs.append("Cần đúng 1 node Start (chưa có)")
    elif len(starts) > 1: errs.append(f"Chỉ được 1 node Start (đang có {len(starts)}: {', '.join(n['id'] for n in starts)})")
    if not ends: errs.append("Cần ít nhất 1 node End")
    fields = {f["name"] for f in wf.get("state", [])}
    for e in edges:
        missing = [x for x in (e["source"], e["target"]) if x not in ids]
        if missing:
            errs.append(f"Edge {e.get('id')} trỏ tới node không tồn tại: {', '.join(missing)}")
        elif e["source"] == e["target"] and types.get(e["source"]) != "condition":
            errs.append(f"Node {e['source']}: không được tự nối vào chính nó (chỉ Condition mới được tạo vòng lặp)")
    edges = [e for e in edges if e["source"] in ids and e["target"] in ids]
    out = {i: [e for e in edges if e["source"] == i] for i in ids}
    for n in nodes:
        t, d, nid = n.get("type"), n.get("data", {}), n["id"]
        if t not in ("start", "llm", "tool", "condition", "end"):
            errs.append(f"Node {nid}: type không hợp lệ '{t}'")
        if t != "end" and not out.get(nid):
            errs.append(f"Node {nid} ({d.get('label', t)}) không có cạnh ra")
        if t == "end" and out.get(nid):
            errs.append(f"Node End {nid} không được có cạnh ra")
        if t == "start" and any(e["target"] == nid for e in edges):
            errs.append("Start không được có cạnh vào")
        if t in ("llm", "tool"):
            if len(out.get(nid, [])) > 1:
                errs.append(f"Node {nid}: chỉ được 1 cạnh ra (dùng Condition để rẽ nhánh)")
            of = d.get("output_field")
            if not of: errs.append(f"Node {nid}: thiếu output_field")
            elif fields and of not in fields: errs.append(f"Node {nid}: output_field '{of}' không có trong state")
        if t == "tool":
            if d.get("mode", "function") == "function" and d.get("function") not in TOOLS:
                errs.append(f"Node {nid}: function '{d.get('function')}' chưa đăng ký")
            if d.get("mode") == "http" and not d.get("url"):
                errs.append(f"Node {nid}: thiếu URL")
        if t == "condition":
            if not d.get("field"): errs.append(f"Node {nid}: Condition thiếu field")
            labels = [e.get("label") for e in out.get(nid, [])]
            if any(not l for l in labels): errs.append(f"Node {nid}: mọi cạnh ra từ Condition cần label")
            if len(set(labels)) != len(labels): errs.append(f"Node {nid}: label trùng")
        if t == "llm":
            for v in VAR_RE.findall(d.get("prompt", "")):
                if fields and v not in fields: errs.append(f"Node {nid}: biến state.{v} không có trong state")
    # cycles must pass through a Condition node (otherwise the loop can never exit)
    plain = {i: [e["target"] for e in out.get(i, []) if types.get(e["target"]) != "condition" and e["target"] != i] for i in ids if types.get(i) != "condition"}
    state_: Dict[str, int] = {}
    def dfs(u, path):
        state_[u] = 1; path.append(u)
        for v in plain.get(u, []):
            if state_.get(v) == 1:
                cyc = path[path.index(v):] + [v]
                errs.append(f"Vòng lặp không qua Condition: {' → '.join(cyc)}")
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
            if n["id"] not in seen: errs.append(f"Node {n['id']} không đi tới được từ Start")
    return errs


# ---------------- Compile ----------------
def _node_fn(node: Dict[str, Any]):
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


def compile_workflow(wf: Dict[str, Any]):
    errs = validate(wf)
    if errs: raise ValidationError(errs)
    ann = {f["name"]: Optional[TYPE_MAP.get(f.get("type", "string"), str)] for f in wf.get("state", [])}
    State = TypedDict("State", ann, total=False)  # type: ignore
    g = StateGraph(State)
    nodes = {n["id"]: n for n in wf["nodes"]}
    for nid, n in nodes.items():
        g.add_node(nid, _node_fn(n))
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
                raise ValueError(f"Condition '{label}' ({nid}): giá trị {field}='{v[:100]}' không khớp label nào {list(mapping)} và không có default")
            g.add_conditional_edges(nid, router, mapping)
        else:
            for e in out:
                g.add_edge(nid, e["target"])
    return g.compile()


RECURSION_LIMIT = int(os.environ.get("STUDIO_RECURSION_LIMIT", 25))  # max super-steps per run (loops)
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
    if not isinstance(inputs, dict): return ["Input phải là một JSON object, ví dụ {\"message\": \"hi\"}"]
    errs = []
    for f in wf.get("state", []) or []:
        name, typ = f.get("name"), f.get("type", "string")
        if name in inputs and inputs[name] is not None and typ in PY_TYPES:
            v = inputs[name]; ok = isinstance(v, PY_TYPES[typ]) and not (typ in ("number", "integer") and isinstance(v, bool))
            if not ok: errs.append(f"Input '{name}' phải có kiểu {typ} (nhận {type(v).__name__})")
    return errs


def run_stream(wf: Dict[str, Any], inputs: Dict[str, Any]):
    """Yield per-node events: started / finished(duration, input=state before, delta=output) / error. Sync generator."""
    if (bad := check_input(wf, inputs)): raise ValidationError(bad)
    app = compile_workflow(wf)
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
        for chunk in app.stream(inputs, {"recursion_limit": RECURSION_LIMIT}, stream_mode="updates"):
            before = dict(state)
            for nid, delta in chunk.items():
                delta = delta or {}
                state.update(delta)
                yield {"type": "node_finished", **meta(nid), "iteration": counts.get(nid, 1),
                       "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
                       "input": cap_payload(before), "delta": cap_payload(delta)}
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
               "errors": [safe_error(e)]}
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
