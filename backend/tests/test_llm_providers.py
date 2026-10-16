import copy, json, sqlite3, uuid
import httpx, pytest
from fastapi.testclient import TestClient
from app.core import crypto as creds
from app.core.config import STUDIO_DB as DB
from app.engine import llm as compiler
from app.engine.compiler import compile_workflow
from app.engine.examples import EXAMPLE
from app.main import app

c = TestClient(app)
SECRET_OAI = "sk-test-openai-0123456789abcdef"
SECRET_ANT = "sk-ant-test-abcdef0123456789"

def H(t): return {"Authorization": f"Bearer {t}"}
def user():
    email = f"llm{uuid.uuid4().hex[:6]}@example.com"
    return c.post("/api/auth/register", json={"email": email, "password": "secret12"}).json()["token"]

@pytest.fixture
def mock_http(monkeypatch):
    calls = []
    def handler(req: httpx.Request):
        calls.append(req)
        body = json.loads(req.content)
        if req.url.host == "fail.example": return httpx.Response(401, json={"error": {"message": "invalid api key"}})
        if req.url.path.endswith("/chat/completions"):
            prompt = body["messages"][0]["content"]
            return httpx.Response(200, json={"choices": [{"message": {"content": "order_status" if "Classify" in prompt else f"OAI:{body['model']}"}}]})
        if req.url.path == "/v1/messages":
            return httpx.Response(200, json={"content": [{"type": "text", "text": f"ANT:{body['model']}"}]})
        return httpx.Response(404)
    monkeypatch.setattr(compiler, "http_client", lambda: httpx.Client(transport=httpx.MockTransport(handler)))
    return calls

def run_ws(tok, wid, inp):
    with c.websocket_connect(f"/ws/run?token={tok}") as ws:
        ws.send_json({"workflow_id": wid, "input": inp}); evs = []
        while True:
            evs.append(ws.receive_json())
            if evs[-1]["type"] in ("run_finished", "error"): return evs

def wf_with(tok, cred_id, model="gpt-4o-mini"):
    wf = copy.deepcopy(EXAMPLE)
    for n in wf["nodes"]:
        if n["type"] == "llm": n["data"].update(credential_id=cred_id, model=model)
    return c.post("/api/workflows", json=wf, headers=H(tok)).json()["id"]

def test_encrypted_at_rest_and_never_returned():
    t = user()
    r = c.post("/api/credentials", json={"name": "oai", "provider": "openai", "api_key": SECRET_OAI}, headers=H(t))
    assert r.status_code == 200 and SECRET_OAI not in r.text and r.json()["hint"].endswith("cdef")
    assert SECRET_OAI not in c.get("/api/credentials", headers=H(t)).text
    raw = sqlite3.connect(DB).execute("SELECT secret FROM credentials WHERE id=?", (r.json()["id"],)).fetchone()[0]
    assert SECRET_OAI not in raw and creds.decrypt(raw) == SECRET_OAI

def test_validation_errors():
    t = user()
    assert c.post("/api/credentials", json={"name": "x", "provider": "nope", "api_key": "k"}, headers=H(t)).status_code == 400
    assert c.post("/api/credentials", json={"name": "x", "provider": "openai", "api_key": " "}, headers=H(t)).status_code == 400
    assert c.get("/api/credentials").status_code == 401

def test_openai_run_uses_credential(mock_http):
    t = user()
    cid = c.post("/api/credentials", json={"name": "oai", "provider": "openai", "api_key": SECRET_OAI, "base_url": "https://llm.example/v1"}, headers=H(t)).json()["id"]
    evs = run_ws(t, wf_with(t, cid), {"message": "A100?"})
    assert evs[-1]["type"] == "run_finished", evs[-1]
    st = evs[-1]["state"]
    assert st["intent"] == "order_status" and st["answer"] == "OAI:gpt-4o-mini" and "A100" in st["tool_result"]
    assert mock_http and all(r.headers["authorization"] == f"Bearer {SECRET_OAI}" and r.url.host == "llm.example" for r in mock_http)
    assert SECRET_OAI not in json.dumps(evs)

def test_anthropic_provider(mock_http):
    out = compiler.call_llm("hi", "claude-x", {"provider": "anthropic", "api_key": SECRET_ANT, "base_url": "https://api.anthropic.com"})
    assert out == "ANT:claude-x" and mock_http[0].headers["x-api-key"] == SECRET_ANT

def test_provider_error_is_event_without_secret(mock_http):
    t = user()
    cid = c.post("/api/credentials", json={"name": "bad", "provider": "openai", "api_key": SECRET_OAI, "base_url": "https://fail.example/v1"}, headers=H(t)).json()["id"]
    evs = run_ws(t, wf_with(t, cid), {"message": "hi"})
    assert evs[-1]["type"] == "error" and "HTTP 401" in evs[-1]["errors"][0]
    assert SECRET_OAI not in json.dumps(evs)

def test_cannot_use_other_users_credential(mock_http):
    a, b = user(), user()
    cid = c.post("/api/credentials", json={"name": "a", "provider": "openai", "api_key": SECRET_OAI}, headers=H(a)).json()["id"]
    evs = run_ws(b, wf_with(b, cid), {"message": "hi"})
    assert evs[-1]["type"] == "error" and "không thuộc về bạn" in evs[-1]["errors"][0] and not mock_http
    assert c.delete(f"/api/credentials/{cid}", headers=H(b)).status_code == 404
    assert c.delete(f"/api/credentials/{cid}", headers=H(a)).status_code == 200

def test_mock_mode_unchanged_without_credentials(mock_http):
    out = compile_workflow(EXAMPLE).invoke({"message": "order A100"})
    assert out["answer"].startswith("[mock:") and not mock_http
