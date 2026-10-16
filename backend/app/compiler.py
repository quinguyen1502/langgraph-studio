"""Compile workflow JSON {nodes, edges, state} into a LangGraph StateGraph."""
from __future__ import annotations
import json, operator, os, re, time
from typing import Any, Callable, Dict, List, Optional, TypedDict
import httpx
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


class LLMError(Exception):
    pass


def http_client() -> httpx.Client:
    """Factory for outbound LLM HTTP calls (tests replace this with a MockTransport client)."""
    return httpx.Client(timeout=60)


def _post(provider: str, url: str, headers: Dict[str, str], body: Dict[str, Any]) -> Dict[str, Any]:
    try:
        with http_client() as c:
            r = c.post(url, headers=headers, json=body)
    except httpx.HTTPError as e:
        raise LLMError(f"{provider}: không kết nối được ({type(e).__name__})") from None
    if r.status_code >= 400:
        try: msg = r.json().get("error", {}).get("message") or r.text
        except Exception: msg = r.text
        raise LLMError(f"{provider}: HTTP {r.status_code}: {str(msg)[:200]}")
    return r.json()


def call_llm(prompt: str, model: str, cred: Optional[Dict[str, Any]] = None) -> str:
    """cred: decrypted credential {provider, base_url, api_key}. Without cred falls back to env OPENAI_API_KEY, then mock."""
    if cred is None:
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            return mock_llm(prompt, model)
        cred = {"provider": "openai", "api_key": key, "base_url": os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")}
    provider, key, base = cred["provider"], cred["api_key"], (cred.get("base_url") or "").rstrip("/")
    if provider == "anthropic":
        data = _post("anthropic", f"{base or 'https://api.anthropic.com'}/v1/messages",
                     {"x-api-key": key, "anthropic-version": "2023-06-01"},
                     {"model": model or "claude-3-5-haiku-latest", "max_tokens": 1024, "messages": [{"role": "user", "content": prompt}]})
        try: return "".join(b.get("text", "") for b in data["content"] if b.get("type") == "text").strip()
        except Exception: raise LLMError("anthropic: response không hợp lệ") from None
    data = _post("openai", f"{base or 'https://api.openai.com/v1'}/chat/completions", {"Authorization": f"Bearer {key}"},
                 {"model": model or "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}]})
    try: return data["choices"][0]["message"]["content"].strip()
    except Exception: raise LLMError("openai: response không hợp lệ") from None


# ---------------- Validation ----------------
def validate(wf: Dict[str, Any]) -> List[str]:
    errs: List[str] = []
    nodes = wf.get("nodes", [])
    edges = wf.get("edges", [])
    ids = {n["id"] for n in nodes}
    types = {n["id"]: n.get("type") for n in nodes}
    starts = [n for n in nodes if n.get("type") == "start"]
    ends = [n for n in nodes if n.get("type") == "end"]
    if len(starts) != 1: errs.append("Cần đúng 1 node Start")
    if not ends: errs.append("Cần ít nhất 1 node End")
    fields = {f["name"] for f in wf.get("state", [])}
    for e in edges:
        if e["source"] not in ids or e["target"] not in ids:
            errs.append(f"Edge {e.get('id')} trỏ tới node không tồn tại")
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
def _node_fn(node: Dict[str, Any], resolve: Optional[Callable[[str], Dict[str, Any]]] = None):
    t, d = node["type"], node.get("data", {})
    if t == "llm":
        def fn(state):
            cred = None
            if d.get("credential_id"):
                if resolve is None: raise LLMError("Node dùng credential nhưng không có resolver")
                cred = resolve(d["credential_id"])
            return {d["output_field"]: call_llm(render(d.get("prompt", ""), state), d.get("model", "gpt-4o-mini"), cred)}
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


def compile_workflow(wf: Dict[str, Any], resolve: Optional[Callable[[str], Dict[str, Any]]] = None):
    errs = validate(wf)
    if errs: raise ValidationError(errs)
    ann = {f["name"]: Optional[TYPE_MAP.get(f.get("type", "string"), str)] for f in wf.get("state", [])}
    State = TypedDict("State", ann, total=False)  # type: ignore
    g = StateGraph(State)
    nodes = {n["id"]: n for n in wf["nodes"]}
    for nid, n in nodes.items():
        g.add_node(nid, _node_fn(n, resolve))
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
            def router(state, field=field, mapping=mapping, default=default):
                v = str(state.get(field, "")).strip()
                if v in mapping: return v
                for k in mapping:  # case-insensitive / contains fallback
                    if k.lower() == v.lower() or k.lower() in v.lower(): return k
                if default and default in mapping: return default
                raise ValueError(f"Condition: giá trị '{v}' không khớp label nào {list(mapping)}")
            g.add_conditional_edges(nid, router, mapping)
        else:
            for e in out:
                g.add_edge(nid, e["target"])
    return g.compile()


def run_stream(wf: Dict[str, Any], inputs: Dict[str, Any], resolve: Optional[Callable[[str], Dict[str, Any]]] = None):
    """Yield per-node events: started / finished(duration, delta). Sync generator."""
    app = compile_workflow(wf, resolve)
    nodes = {n["id"]: n for n in wf["nodes"]}
    state = dict(inputs)
    start_id = next(n["id"] for n in wf["nodes"] if n["type"] == "start")
    yield {"type": "node_started", "node": start_id, "label": nodes[start_id]["data"].get("label")}
    t0 = time.perf_counter(); pending = start_id
    for chunk in app.stream(inputs, stream_mode="updates"):
        for nid, delta in chunk.items():
            delta = delta or {}
            state.update(delta)
            yield {"type": "node_finished", "node": nid, "label": nodes[nid]["data"].get("label"),
                   "duration_ms": round((time.perf_counter() - t0) * 1000, 2), "delta": delta}
        # predict next node(s) to mark as started
        nxt = _next_nodes(wf, list(chunk)[-1], state)
        t0 = time.perf_counter()
        for n2 in nxt:
            yield {"type": "node_started", "node": n2, "label": nodes[n2]["data"].get("label")}
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
