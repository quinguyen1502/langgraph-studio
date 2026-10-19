"""TASK-0025: template library: built-ins, save-as (sanitised), import/export, use, scopes, delete."""
import uuid
from types import SimpleNamespace as NS
from fastapi.testclient import TestClient
from app.engine import templates as T
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
