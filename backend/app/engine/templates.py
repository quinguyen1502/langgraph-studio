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
        if isinstance(d.get("approval"), dict):  # a Human node keeps only the channel kind, not the connection, target or approvers (TASK-0064)
            d["approval"] = {"channel": d["approval"]["channel"]} if d["approval"].get("channel") else {}
        out["nodes"].append({"id": n["id"], "type": n["type"], "position": n.get("position") or {"x": 0, "y": 0}, "data": d})
    for e in wf.get("edges") or []:
        out["edges"].append({k: e[k] for k in ("id", "source", "target", "label", "conditional", "sourceHandle") if k in e and e[k] not in (None, "")})
    return out


def channels(wf: dict) -> list[str]:
    """The approval channel kinds a graph's Human nodes use, once each, in node order (gallery logos, TASK-0064)."""
    kinds = [((n.get("data") or {}).get("approval") or {}).get("channel") for n in wf.get("nodes") or [] if n.get("type") == "human"]
    return list(dict.fromkeys(k for k in kinds if isinstance(k, str) and k))


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
def _approval(kind: str, name: str, via: str) -> dict:
    """Draft -> Human (asks through `kind`) -> approved: polish / rejected: end (TASK-0064). Only the channel kind is set:
    the user picks the connection, the target and the approvers after creating the workflow."""
    return {"id": f"builtin-approval-{kind}", "name": name, "description": f"Draft a reply and ask for approval {via}.", "workflow": {
        "state": [{"name": "message", "type": "string"}, {"name": "draft", "type": "string"}, {"name": "decision", "type": "string"}, {"name": "answer", "type": "string"}],
        "nodes": [_n("start", "start", 40, 180, label="Start"),
                  _n("draft", "llm", 260, 180, label="Draft reply", model="gpt-4o-mini", output_field="draft", prompt="Draft a reply to: {{state.message}}"),
                  _n("ask", "human", 500, 180, label="Approve the reply", prompt="Approve this reply?\n{{state.draft}}", output_field="decision", approval={"channel": kind}),
                  _n("route", "condition", 740, 180, label="Approved?", field="decision", default="rejected"),
                  _n("send", "llm", 980, 80, label="Polish reply", model="gpt-4o-mini", output_field="answer", prompt="Polish this approved reply: {{state.draft}}"),
                  _n("end", "end", 1220, 180, label="End")],
        "edges": [_e("e1", "start", "draft"), _e("e2", "draft", "ask"), _e("e3", "ask", "route"),
                  _e("e4", "route", "send", "approved"), _e("e5", "route", "end", "rejected"), _e("e6", "send", "end")]}}


BUILTINS += [
    _approval("slack", "Approve in Slack", "with Approve / Reject buttons in Slack"),
    _approval("telegram", "Approve in Telegram", "with Approve / Reject buttons in Telegram"),
    _approval("whatsapp", "Approve in WhatsApp", "with reply buttons in WhatsApp"),
    {"id": "builtin-approval-email", "name": "Approve by e-mail", "description": "Ask for approval by e-mail, then e-mail the requester the result.", "workflow": {
        "state": [{"name": "message", "type": "string"}, {"name": "requester", "type": "string"}, {"name": "draft", "type": "string"},
                  {"name": "decision", "type": "string"}, {"name": "sent", "type": "object"}],
        "nodes": [_n("start", "start", 40, 180, label="Start"),
                  _n("draft", "llm", 260, 180, label="Draft reply", model="gpt-4o-mini", output_field="draft", prompt="Draft a reply to: {{state.message}}"),
                  _n("ask", "human", 500, 180, label="Approve by e-mail", prompt="Approve this reply?\n{{state.draft}}", output_field="decision", approval={"channel": "email"}),
                  _n("route", "condition", 740, 180, label="Approved?", field="decision", default="rejected"),
                  _n("mail", "email", 980, 80, label="E-mail the reply", to="{{state.requester}}", subject="Your request", body="{{state.draft}}", format="text", output_field="sent"),
                  _n("end", "end", 1220, 180, label="End")],
        "edges": [_e("e1", "start", "draft"), _e("e2", "draft", "ask"), _e("e3", "ask", "route"),
                  _e("e4", "route", "mail", "approved"), _e("e5", "route", "end", "rejected"), _e("e6", "mail", "end")]}},
    _approval("teams", "Approve in Microsoft Teams", "with an Adaptive Card in Microsoft Teams"),
    {"id": "builtin-approval-multilevel", "name": "Two-level approval", "description": "A team lead approves in Slack, then a manager approves by e-mail.", "workflow": {
        "state": [{"name": "message", "type": "string"}, {"name": "draft", "type": "string"}, {"name": "lead_decision", "type": "string"},
                  {"name": "decision", "type": "string"}, {"name": "answer", "type": "string"}],
        "nodes": [_n("start", "start", 40, 200, label="Start"),
                  _n("draft", "llm", 260, 200, label="Draft reply", model="gpt-4o-mini", output_field="draft", prompt="Draft a reply to: {{state.message}}"),
                  _n("lead", "human", 500, 200, label="Team lead approval", prompt="Approve this reply?\n{{state.draft}}", output_field="lead_decision", approval={"channel": "slack"}),
                  _n("lead_ok", "condition", 740, 200, label="Lead approved?", field="lead_decision", default="rejected"),
                  _n("manager", "human", 980, 80, label="Manager approval", prompt="The team lead approved this reply. Approve it?\n{{state.draft}}", output_field="decision", approval={"channel": "email"}),
                  _n("manager_ok", "condition", 1220, 80, label="Manager approved?", field="decision", default="rejected"),
                  _n("send", "llm", 1460, 0, label="Polish reply", model="gpt-4o-mini", output_field="answer", prompt="Polish this approved reply: {{state.draft}}"),
                  _n("end", "end", 1700, 200, label="End")],
        "edges": [_e("e1", "start", "draft"), _e("e2", "draft", "lead"), _e("e3", "lead", "lead_ok"),
                  _e("e4", "lead_ok", "manager", "approved"), _e("e5", "lead_ok", "end", "rejected"), _e("e6", "manager", "manager_ok"),
                  _e("e7", "manager_ok", "send", "approved"), _e("e8", "manager_ok", "end", "rejected"), _e("e9", "send", "end")]}},
    {"id": "builtin-support-escalation", "name": "Support with escalation", "description": "Answer from a knowledge base; a person reviews the answers that are unsure.", "workflow": {
        "state": [{"name": "message", "type": "string"}, {"name": "context", "type": "string"}, {"name": "answer", "type": "string"},
                  {"name": "verdict", "type": "string"}, {"name": "review", "type": "string"}],
        "nodes": [_n("start", "start", 40, 200, label="Start"),
                  _n("retrieve", "retriever", 260, 200, label="Search the FAQ", knowledge_base_id="", query="{{state.message}}", top_k=4, output_field="context"),
                  _n("answer", "llm", 500, 200, label="Answer from context", model="gpt-4o-mini", output_field="answer",
                     prompt="Answer using only this context.\n{{state.context}}\nQuestion: {{state.message}}"),
                  _n("check", "decision", 740, 200, label="Is the answer sure?", model="jev-latest", text="Question: {{state.message}}\nAnswer: {{state.answer}}",
                     questions=[{"id": "verdict", "type": "choice", "instructions": "Does the answer fully resolve the question?", "field": "verdict",
                                 "options": [{"label": "answered", "description": "The answer resolves the question from the context"},
                                             {"label": "escalate", "description": "The answer is unsure, or the context does not cover the question"}]}]),
                  _n("route", "condition", 980, 200, label="Escalate?", field="verdict", default="escalate"),
                  _n("review", "human", 1220, 320, label="Support agent review", prompt="Check this answer before it is sent:\n{{state.answer}}", output_field="review"),
                  _n("end", "end", 1460, 200, label="End")],
        "edges": [_e("e1", "start", "retrieve"), _e("e2", "retrieve", "answer"), _e("e3", "answer", "check"), _e("e4", "check", "route"),
                  _e("e5", "route", "end", "answered"), _e("e6", "route", "review", "escalate"), _e("e7", "review", "end")]}},
    {"id": "builtin-batch", "name": "Batch processing", "description": "Summarise each item of a list, then combine the summaries.", "workflow": {
        "state": [{"name": "items", "type": "list"}, {"name": "item", "type": "string"}, {"name": "summaries", "type": "list", "reducer": "append"},
                  {"name": "digest", "type": "string"}],
        "nodes": [_n("start", "start", 40, 200, label="Start"),
                  _n("each", "foreach", 280, 200, label="Each item", items_field="items", item_field="item", max_items=100),
                  _n("summarize", "llm", 540, 60, label="Summarise item", model="gpt-4o-mini", output_field="summaries", prompt="Summarise in one line: {{state.item}}"),
                  _n("combine", "llm", 540, 340, label="Combine summaries", model="gpt-4o-mini", output_field="digest",
                     prompt="Write a short digest from:\n{{state.summaries | join(\"\\n\")}}"),
                  _n("end", "end", 800, 340, label="End")],
        "edges": [_e("e1", "start", "each"), _e("e2", "each", "summarize", "each"), _e("e3", "summarize", "each"),
                  _e("e4", "each", "combine", "done"), _e("e5", "combine", "end")]}},
]
BUILTIN_IDS = {b["id"] for b in BUILTINS}
