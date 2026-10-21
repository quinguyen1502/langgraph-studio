"""TASK-0025: template library: built-ins, save-as (sanitised), import/export, use, scopes, delete."""
import uuid
import pytest
from types import SimpleNamespace as NS
from fastapi.testclient import TestClient
from app.engine import templates as T
from app.engine.runtime import run_stream
from app.engine.validator import validate
from app.main import app

c = TestClient(app)
H = lambda t: {"Authorization": f"Bearer {t}"}
code = lambda r: r.json()["error"]["code"]


def register():
    email = f"t{uuid.uuid4().hex[:6]}@example.com"
    d = c.post("/api/auth/register", json={"email": email, "password": "secret12"}).json()["data"]
    return NS(token=d["token"], id=d["user"]["id"])


def admin():
    return NS(token=c.post("/api/auth/login", json={"email": "admin@example.com", "password": "admin123"}).json()["data"]["token"])


SECRETY = {"name": "Secrety", "state": [{"name": "message", "type": "string"}, {"name": "out", "type": "string"}],
           "nodes": [{"id": "start", "type": "start", "position": {"x": 0, "y": 0}, "data": {"label": "Start"}},
                     {"id": "call", "type": "tool", "position": {"x": 200, "y": 0},
                      "data": {"label": "Call", "mode": "http", "url": "https://x.example", "credential_id": "cred-1",
                               "headers": {"Authorization": "Bearer abc"}, "api_key": "sk-1", "_status": "ok", "output_field": "out"}},
                     {"id": "end", "type": "end", "position": {"x": 400, "y": 0}, "data": {"label": "End"}}],
           "edges": [{"id": "e1", "source": "start", "target": "call"}, {"id": "e2", "source": "call", "target": "end"}]}


def test_sanitize_strips_refs_secrets_and_runtime():
    g = T.sanitize(SECRETY)
    d = g["nodes"][1]["data"]
    assert d["credential_id"] == "" and "headers" not in d and "api_key" not in d and "_status" not in d
    assert d["url"] == "https://x.example" and "name" not in g and SECRETY["nodes"][1]["data"]["api_key"] == "sk-1"  # input untouched


def test_builtins_are_well_formed():
    for b in T.BUILTINS:
        assert T.problems(T.export_payload(b["name"], b["description"], b["workflow"])) == []
        assert all("knowledge base" in e for e in validate(b["workflow"]))  # only "pick your KB" may remain


NEW = ["builtin-approval-slack", "builtin-approval-telegram", "builtin-approval-whatsapp", "builtin-approval-email", "builtin-approval-teams",
       "builtin-approval-multilevel", "builtin-support-escalation", "builtin-batch"]
FIRST_HUMAN = {**{i: "ask" for i in NEW[:5]}, "builtin-approval-multilevel": "lead"}
INPUTS = {"message": "Where is my order?", "requester": "ann@example.com", "items": ["Release 1.0: new editor", "Release 1.1: faster runs"]}


def test_builtin_order_and_channel_kinds():
    """TASK-0064: 12 built-ins, the eight new ones after the first four. Human nodes on a channel store only its kind."""
    assert [b["id"] for b in T.BUILTINS] == ["builtin-chatbot", "builtin-rag", "builtin-approval", "builtin-router", *NEW]
    kinds = {b["id"]: [n["data"]["approval"] for n in b["workflow"]["nodes"] if n["type"] == "human" and "approval" in n["data"]] for b in T.BUILTINS}
    assert {i: [a["channel"] for a in v] for i, v in kinds.items() if v} == {
        "builtin-approval-slack": ["slack"], "builtin-approval-telegram": ["telegram"], "builtin-approval-whatsapp": ["whatsapp"],
        "builtin-approval-email": ["email"], "builtin-approval-teams": ["teams"], "builtin-approval-multilevel": ["slack", "email"]}
    assert all(list(a) == ["channel"] for v in kinds.values() for a in v)
    ts = {t["id"]: t["channels"] for t in c.get("/api/templates", headers=H(register().token)).json()["data"]}
    assert ts["builtin-approval-multilevel"] == ["slack", "email"] and ts["builtin-approval-teams"] == ["teams"] and ts["builtin-chatbot"] == []


@pytest.mark.parametrize("tid", [i for i in NEW if i != "builtin-support-escalation"])  # that one needs a knowledge base, like builtin-rag
def test_new_builtins_run_offline(tid, monkeypatch):
    """Mock LLM and dry-run e-mail: each runs up to its first Human node, or to the end."""
    for k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "TYPESAFE_API_KEY"): monkeypatch.delenv(k, raising=False)
    wf = next(b for b in T.BUILTINS if b["id"] == tid)["workflow"]
    evs = list(run_stream(wf, {k: v for k, v in INPUTS.items() if any(f["name"] == k for f in wf["state"])}))
    assert not [e for e in evs if e["type"] == "error"]
    if tid in FIRST_HUMAN: assert evs[-1]["type"] == "run_waiting" and evs[-1]["node"] == FIRST_HUMAN[tid]
    else: assert evs[-1]["type"] == "run_finished" and len(evs[-1]["state"]["summaries"]) == 2 and evs[-1]["state"]["digest"]


def test_channel_template_waits_in_the_studio_without_a_connection():
    """A workflow made from a channel template keeps the kind and, with no connection yet, waits to be approved in the studio."""
    u = register(); wid = c.post("/api/templates/builtin-approval-slack/use", headers=H(u.token), json={}).json()["data"]["id"]
    wf = c.get(f"/api/workflows/{wid}", headers=H(u.token)).json()["data"]
    assert next(n for n in wf["nodes"] if n["id"] == "ask")["data"]["approval"] == {"channel": "slack"}
    with c.websocket_connect(f"/ws/run?token={u.token}") as ws:
        ws.send_json({"workflow_id": wid, "input": {"message": "hi"}}); evs = []
        while not evs or evs[-1]["type"] not in ("run_finished", "run_waiting", "error"): evs.append(ws.receive_json())
    assert evs[-1]["type"] == "run_waiting" and evs[-1]["node"] == "ask"


def test_sanitize_keeps_only_the_channel_kind():
    """Saved and exported templates drop a Human node's connection, target and approvers (TASK-0064)."""
    wf = {"nodes": [{"id": "a", "type": "human", "data": {"approval": {"channel_id": "c1", "channel": "slack", "target": "C1", "approvers": ["x@y.z"]}}},
                    {"id": "b", "type": "human", "data": {"approval": {"channel_id": "c2"}}}], "edges": []}
    assert [n["data"]["approval"] for n in T.sanitize(wf)["nodes"]] == [{"channel": "slack"}, {}]


def test_problems():
    assert T.problems([]) == ["not a JSON object"]
    bad = {"format": T.FORMAT, "version": 1, "workflow": {"nodes": [{"id": "a", "type": "llm"}], "edges": [{"source": "a", "target": "zz"}]}}
    errs = T.problems(bad)
    assert any("Start" in e for e in errs) and any("edge" in e for e in errs)
    assert T.problems({"format": "x", "version": 2, "workflow": {}})[:2] == ["format must be 'superstep/template'", "unsupported version 2"]


def test_list_use_builtin():
    u = register()
    ts = c.get("/api/templates", headers=H(u.token)).json()["data"]
    assert [t["id"] for t in ts[:4]] == ["builtin-chatbot", "builtin-rag", "builtin-approval", "builtin-router"]
    assert ts[0]["nodes"] and "data" not in ts[0]["nodes"][0]  # preview only
    r = c.post("/api/templates/builtin-chatbot/use", headers=H(u.token), json={}).json()["data"]
    r2 = c.post("/api/templates/builtin-chatbot/use", headers=H(u.token)).json()["data"]
    names = {w["id"]: w["name"] for w in c.get("/api/workflows", headers=H(u.token)).json()["data"]}
    assert names[r["id"]] == "Chatbot" and names[r2["id"]] != "Chatbot" and r["errors"] == []
    assert code(c.post("/api/templates/nope/use", headers=H(u.token))) == "TEMPLATE_NOT_FOUND"


def test_save_as_export_import_delete():
    u, other = register(), register()
    wid = c.post("/api/workflows", headers=H(u.token), json=SECRETY).json()["data"]["id"]
    t = c.post("/api/templates", headers=H(u.token), json={"workflow_id": wid, "name": "  My  tpl ", "description": "d"}).json()["data"]
    assert t["name"] == "My tpl" and t["scope"] == "user" and t["mine"] and t["deletable"]
    exp = c.get(f"/api/templates/{t['id']}/export", headers=H(u.token)).json()["data"]
    assert exp["format"] == T.FORMAT and "sk-1" not in str(exp) and "cred-1" not in str(exp)
    # private: other users can't see, export, use or delete it
    assert t["id"] not in [x["id"] for x in c.get("/api/templates", headers=H(other.token)).json()["data"]]
    for r in (c.get(f"/api/templates/{t['id']}/export", headers=H(other.token)), c.delete(f"/api/templates/{t['id']}", headers=H(other.token))):
        assert code(r) == "TEMPLATE_NOT_FOUND"
    # other can't save someone else's workflow as a template
    assert c.post("/api/templates", headers=H(other.token), json={"workflow_id": wid, "name": "x"}).status_code in (403, 404)
    imp = c.post("/api/templates/import", headers=H(other.token), json={"file": exp}).json()["data"]
    assert imp["name"] == "My tpl" and imp["mine"]
    bad = c.post("/api/templates/import", headers=H(other.token), json={"file": {"format": "nope"}})
    assert code(bad) == "TEMPLATE_INVALID" and bad.json()["error"]["details"]
    assert code(c.post("/api/templates", headers=H(u.token), json={"workflow_id": wid, "name": "  "})) == "TEMPLATE_NAME_REQUIRED"
    assert code(c.delete("/api/templates/builtin-rag", headers=H(u.token))) == "TEMPLATE_READ_ONLY"
    assert c.delete(f"/api/templates/{t['id']}", headers=H(u.token)).json()["data"] == {"ok": True}
    assert code(c.delete(f"/api/templates/{t['id']}", headers=H(u.token))) == "TEMPLATE_NOT_FOUND"


def test_org_scope_needs_admin():
    u, a = register(), admin()
    wid = c.post("/api/workflows", headers=H(u.token), json=SECRETY).json()["data"]["id"]
    assert code(c.post("/api/templates", headers=H(u.token), json={"workflow_id": wid, "name": "Org", "scope": "org"})) == "TEMPLATE_SCOPE_FORBIDDEN"
    awid = c.post("/api/workflows", headers=H(a.token), json=SECRETY).json()["data"]["id"]
    t = c.post("/api/templates", headers=H(a.token), json={"workflow_id": awid, "name": "Org wide", "scope": "org"}).json()["data"]
    seen = {x["id"]: x for x in c.get("/api/templates", headers=H(u.token)).json()["data"]}
    assert seen[t["id"]]["scope"] == "org" and not seen[t["id"]]["deletable"]
    assert code(c.delete(f"/api/templates/{t['id']}", headers=H(u.token))) == "TEMPLATE_READ_ONLY"
    assert c.post(f"/api/templates/{t['id']}/use", headers=H(u.token)).json()["data"]["id"]
    assert c.delete(f"/api/templates/{t['id']}", headers=H(a.token)).json()["data"]["ok"]


def test_v010_format_still_imports():
    b = T.BUILTINS[0]
    old = {**T.export_payload(b["name"], b["description"], b["workflow"]), "format": "langgraph-studio/template"}
    assert T.problems(old) == [] and T.export_payload("x", None, b["workflow"])["format"] == "superstep/template"
