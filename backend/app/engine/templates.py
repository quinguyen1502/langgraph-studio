"""Workflow templates (TASK-0025, DEC-0028): built-in starters, the sanitiser shared by save-as/export/import, and the
portable file format. Pure functions; persistence and permissions live in TemplateService."""
from __future__ import annotations
import copy

FORMAT, VERSION = "superstep/template", 1
FORMATS = (FORMAT, "langgraph-studio/template")  # files exported by v0.1.0 still import (TASK-0058)

# node data fields that point at per-user resources or secrets: never copied into a template
REF_FIELDS = ("credential_id", "knowledge_base_id", "server_id", "channel_id", "workflow_id")
SECRET_KEYS = ("headers", "api_key", "secret", "token", "password", "authorization")


def sanitize(wf: dict) -> dict:
    """The graph only (state, nodes, edges), with resource references blanked and secret-like keys and runtime `_` fields
    removed. The receiving user picks their own credential / knowledge base / server / channel / subgraph."""
    out = {"state": copy.deepcopy(wf.get("state") or []), "nodes": [], "edges": []}
    for n in wf.get("nodes") or []:
        d = {k: copy.deepcopy(v) for k, v in (n.get("data") or {}).items()
             if not k.startswith("_") and k.lower() not in SECRET_KEYS}
        for f in REF_FIELDS:
            if f in d: d[f] = ""
        out["nodes"].append({"id": n["id"], "type": n["type"], "position": n.get("position") or {"x": 0, "y": 0}, "data": d})
    for e in wf.get("edges") or []:
        out["edges"].append({k: e[k] for k in ("id", "source", "target", "label", "conditional", "sourceHandle") if k in e and e[k] not in (None, "")})
    return out


def export_payload(name: str, description: str | None, graph: dict) -> dict:
    return {"format": FORMAT, "version": VERSION, "name": name, "description": description or "", "workflow": sanitize(graph)}


def problems(payload) -> list[str]:
    """Why an imported file is not a template (empty = fine). Structural only; the editor validates the graph on save."""
    if not isinstance(payload, dict): return ["not a JSON object"]
    errs = []
    if payload.get("format") not in FORMATS: errs.append(f"format must be {FORMAT!r}")
    if payload.get("version") != VERSION: errs.append(f"unsupported version {payload.get('version')!r}")
    wf = payload.get("workflow")
    if not isinstance(wf, dict): return errs + ["missing workflow"]
    nodes = wf.get("nodes") if isinstance(wf.get("nodes"), list) else None
    if nodes is None or not all(isinstance(n, dict) and n.get("id") and n.get("type") for n in nodes): return errs + ["nodes must be a list of {id, type}"]
    types = [n["type"] for n in nodes]
    if "start" not in types or "end" not in types: errs.append("a Start and an End node are required")
    ids = {n["id"] for n in nodes}
    if len(ids) != len(nodes): errs.append("node ids must be unique")
    for e in wf.get("edges") or []:
        if not isinstance(e, dict) or e.get("source") not in ids or e.get("target") not in ids: errs.append("every edge must connect existing nodes"); break
    return errs


def _n(i, t, x, y, **data): return {"id": i, "type": t, "position": {"x": x, "y": y}, "data": data}
def _e(i, s, t, label=None): return {"id": i, "source": s, "target": t, **({"label": label} if label else {})}


BUILTINS: list[dict] = [
    {"id": "builtin-chatbot", "name": "Chatbot", "description": "One LLM answers the user's message.", "workflow": {
        "state": [{"name": "message", "type": "string"}, {"name": "answer", "type": "string"}],
        "nodes": [_n("start", "start", 40, 160, label="Start"),
                  _n("reply", "llm", 300, 160, label="Reply", model="gpt-4o-mini", output_field="answer",
                     prompt="You are a helpful assistant. Answer briefly.\nUser: {{state.message}}"),
                  _n("end", "end", 560, 160, label="End")],
        "edges": [_e("e1", "start", "reply"), _e("e2", "reply", "end")]}},
    {"id": "builtin-rag", "name": "RAG Q&A", "description": "Retrieve passages from a knowledge base, then answer with them.", "workflow": {
        "state": [{"name": "message", "type": "string"}, {"name": "context", "type": "string"}, {"name": "answer", "type": "string"}],
        "nodes": [_n("start", "start", 40, 160, label="Start"),
                  _n("retrieve", "retriever", 280, 160, label="Search the FAQ", knowledge_base_id="", query="{{state.message}}", top_k=4, output_field="context"),
                  _n("answer", "llm", 540, 160, label="Answer from context", model="gpt-4o-mini", output_field="answer",
                     prompt="Answer using only this context.\n{{state.context}}\nQuestion: {{state.message}}"),
                  _n("end", "end", 800, 160, label="End")],
        "edges": [_e("e1", "start", "retrieve"), _e("e2", "retrieve", "answer"), _e("e3", "answer", "end")]}},
    {"id": "builtin-approval", "name": "Approval flow", "description": "Draft a reply, ask a human to approve it, then send or revise.", "workflow": {
        "state": [{"name": "message", "type": "string"}, {"name": "draft", "type": "string"}, {"name": "decision", "type": "string"}, {"name": "answer", "type": "string"}],
        "nodes": [_n("start", "start", 40, 180, label="Start"),
                  _n("draft", "llm", 260, 180, label="Draft reply", model="gpt-4o-mini", output_field="draft", prompt="Draft a reply to: {{state.message}}"),
                  _n("ask", "human", 500, 180, label="Supervisor approval", prompt="Approve this reply?\n{{state.draft}}", output_field="decision"),
                  _n("route", "condition", 740, 180, label="Approved?", field="decision", default="rejected"),
                  _n("send", "llm", 980, 80, label="Polish reply", model="gpt-4o-mini", output_field="answer", prompt="Polish this approved reply: {{state.draft}}"),
                  _n("end", "end", 1220, 180, label="End")],
        "edges": [_e("e1", "start", "draft"), _e("e2", "draft", "ask"), _e("e3", "ask", "route"),
                  _e("e4", "route", "send", "approved"), _e("e5", "route", "end", "rejected"), _e("e6", "send", "end")]}},
    {"id": "builtin-router", "name": "Router", "description": "Classify the request and route it to a specialised branch.", "workflow": {
        "state": [{"name": "message", "type": "string"}, {"name": "intent", "type": "string"}, {"name": "answer", "type": "string"}],
        "nodes": [_n("start", "start", 40, 200, label="Start"),
                  _n("classify", "llm", 260, 200, label="Classify", model="gpt-4o-mini", output_field="intent",
                     prompt="Reply with exactly one label: billing, technical or other.\n{{state.message}}"),
                  _n("route", "condition", 500, 200, label="Route", field="intent", default="other"),
                  _n("billing", "llm", 740, 60, label="Billing answer", model="gpt-4o-mini", output_field="answer", prompt="Answer the billing question: {{state.message}}"),
                  _n("technical", "llm", 740, 200, label="Technical answer", model="gpt-4o-mini", output_field="answer", prompt="Answer the technical question: {{state.message}}"),
                  _n("other", "llm", 740, 340, label="General answer", model="gpt-4o-mini", output_field="answer", prompt="Answer: {{state.message}}"),
                  _n("end", "end", 980, 200, label="End")],
        "edges": [_e("e1", "start", "classify"), _e("e2", "classify", "route"), _e("e3", "route", "billing", "billing"),
                  _e("e4", "route", "technical", "technical"), _e("e5", "route", "other", "other"),
                  _e("e6", "billing", "end"), _e("e7", "technical", "end"), _e("e8", "other", "end")]}},
]
BUILTIN_IDS = {b["id"] for b in BUILTINS}
