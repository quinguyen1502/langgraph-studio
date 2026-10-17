"""TASK-0022: approval of waiting runs through Slack / Telegram, with mocked platform APIs and signed callbacks."""
import hashlib, hmac, json, re, time, uuid
from urllib.parse import urlencode
import httpx, pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.deps import approval_service
from app.services.approval_channels import ADAPTERS
from tests.test_hitl import APPROVAL

SIGNING = "8f742231b10e8888abcd99yyyzzz85a5".replace("y", "1").replace("z", "2")
SLACK = {"bot_token": "xoxb-1111-2222-abcdefgh", "signing_secret": SIGNING}
TG = {"bot_token": "123456:AAbbCCddEEffGGhhIIjjKKll", "webhook_secret": "tg-secret-0123456789abcdef"}


class FakeApi:
    """Records every call to the Slack/Telegram APIs and answers like them."""
    def __init__(self): self.calls: list[tuple[str, dict]] = []
    def __call__(self, req: httpx.Request) -> httpx.Response:
        body = json.loads(req.content or b"{}"); path = req.url.path; self.calls.append((str(req.url), body))
        if path.endswith("chat.postMessage"): return httpx.Response(200, json={"ok": True, "channel": body["channel"], "ts": f"{time.time():.6f}"})
        if path.endswith("sendMessage"): return httpx.Response(200, json={"ok": True, "result": {"message_id": len(self.calls), "chat": {"id": int(body["chat_id"])}}})
        if "fail" in json.dumps(body): return httpx.Response(200, json={"ok": False, "error": "channel_not_found"})
        return httpx.Response(200, json={"ok": True, "result": True})
    def named(self, name): return [b for u, b in self.calls if u.split("?")[0].endswith(name)]
    def requests(self, name="chat.postMessage"):
        """Approval requests only (messages with buttons), not identity-code DMs."""
        return [b for b in self.named(name) if "blocks" in b or "reply_markup" in b]


@pytest.fixture(scope="module")
def c():
    with TestClient(app) as client: yield client

@pytest.fixture(autouse=True)
def api(monkeypatch):
    fake = FakeApi()
    import app.services.approval_service as mod
    monkeypatch.setattr(mod, "BACKGROUND", False)  # send/edit inline: each test sees only its own platform calls
    for a in ADAPTERS.values(): monkeypatch.setattr(a, "transport", httpx.MockTransport(fake), raising=False)
    return fake

def H(t): return {"Authorization": f"Bearer {t}"}
def user(c):
    d = c.post("/api/auth/register", json={"email": f"a{uuid.uuid4().hex[:6]}@example.com", "password": "secret12"}).json()["data"]
    return {"token": d["token"], **d["user"]}

def until(fn, timeout=10):
    t0 = time.time()
    while time.time() - t0 < timeout:
        v = fn()
        if v: return v
        time.sleep(0.05)
    raise AssertionError("timed out")

def workflow(c, owner, approval):
    wf = json.loads(json.dumps(APPROVAL)); wf["name"] = f"Refund {uuid.uuid4().hex[:4]}"; wf["nodes"][1]["data"]["approval"] = approval
    return c.post("/api/workflows", json=wf, headers=H(owner["token"])).json()["data"]["id"]

def start_waiting(c, owner, wid):
    with c.websocket_connect(f"/ws/run?token={owner['token']}") as w:
        w.send_json({"workflow_id": wid, "input": {"message": "order A100"}}); evs = []
        while (evs := evs + [w.receive_json()])[-1]["type"] != "run_summary": pass
    assert evs[-1]["status"] == "waiting"; return evs[0]["run_id"]

def slack_post(c, cid, payload, secret=SIGNING, ts=None):
    body = urlencode({"payload": json.dumps(payload)}).encode(); ts = str(int(ts or time.time()))
    sig = "v0=" + hmac.new(secret.encode(), f"v0:{ts}:".encode() + body, hashlib.sha256).hexdigest()
    return c.post(f"/api/approvals/callback/slack/{cid}", content=body, headers={"Content-Type": "application/x-www-form-urlencoded",
                                                                              "X-Slack-Request-Timestamp": ts, "X-Slack-Signature": sig})

def press(token, uid, action="approve"):
    return {"type": "block_actions", "user": {"id": uid}, "response_url": "https://hooks.slack.com/actions/T1/1/x",
            "actions": [{"action_id": action, "value": token}]}

def code_for(api, external_id):
    """The last verification code the bot DMed to this chat account."""
    msgs = [b.get("text", "") for _, b in api.calls if str(b.get("channel") or b.get("chat_id") or "") == external_id and "code" in b.get("text", "")]
    return re.search(r"\b(\d{6})\b", msgs[-1]).group(1)

def link(c, api, u, kind, external_id, own_channel=True):
    """Link + verify a chat account the way a user does: (own channel to receive the DM) -> link -> code -> verify."""
    if own_channel: c.put(f"/api/approvals/channels/{kind}", json=SLACK if kind == "slack" else TG, headers=H(u["token"]))
    assert c.put("/api/approvals/identities", json={kind: external_id}, headers=H(u["token"])).status_code == 200
    assert c.post(f"/api/approvals/identities/{kind}/send-code", headers=H(u["token"])).status_code == 200
    r = c.post(f"/api/approvals/identities/{kind}/verify", json={"code": code_for(api, external_id)}, headers=H(u["token"]))
    assert r.json()["data"][kind]["verified"] is True, r.json()

def run_row(c, owner, wid, rid): return next(r for r in c.get(f"/api/workflows/{wid}/runs", headers=H(owner["token"])).json()["data"] if r["id"] == rid)


def test_channel_settings_are_validated_encrypted_and_masked(c):
    o = user(c)
    r = c.put("/api/approvals/channels/slack", json={"bot_token": "nope"}, headers=H(o["token"]))
    assert r.status_code == 400 and r.json()["error"] == {"code": "CHANNEL_CONFIG_INVALID", "message": "Channel setting bot_token is missing or invalid", "details": {"field": "bot_token"}}
    assert c.put("/api/approvals/channels/whatsapp", json={}, headers=H(o["token"])).json()["error"]["code"] == "CHANNEL_KIND_UNSUPPORTED"
    ch = c.put("/api/approvals/channels/slack", json=SLACK, headers=H(o["token"])).json()["data"]
    assert ch["hint"] == "••••efgh" and ch["callback_path"] == f"/api/approvals/callback/slack/{ch['id']}" and "bot_token" not in json.dumps(ch)
    tg = c.put("/api/approvals/channels/telegram", json={"bot_token": TG["bot_token"]}, headers=H(o["token"])).json()["data"]
    assert tg["kind"] == "telegram"  # webhook secret generated when left empty
    from app.repositories import ApprovalRepository
    from app.api.deps import get_db
    row = ApprovalRepository(get_db()).channel(ch["id"]); assert SLACK["bot_token"] not in row.secrets  # Fernet at rest
    listed = c.get("/api/approvals/channels", headers=H(o["token"])).json()["data"]
    assert {k["kind"]: bool(k["channel"]) for k in listed["kinds"]} == {"slack": True, "telegram": True}
    assert c.delete("/api/approvals/channels/telegram", headers=H(o["token"])).json()["data"] == {"ok": True}
    assert c.delete("/api/approvals/channels/telegram", headers=H(o["token"])).json()["error"]["code"] == "CHANNEL_NOT_FOUND"
    assert c.post("/api/approvals/channels/slack/register-webhook", headers=H(o["token"])).json()["error"]["code"] == "CHANNEL_PUBLIC_URL_REQUIRED"


def test_identity_is_verified_with_a_one_time_code(c, api, monkeypatch):
    a, b = user(c), user(c); uid = f"U{uuid.uuid4().hex[:8].upper()}"
    assert c.put("/api/approvals/identities", json={"slack": "lower"}, headers=H(a["token"])).json()["error"]["code"] == "IDENTITY_INVALID"
    assert c.post("/api/approvals/identities/slack/send-code", headers=H(a["token"])).json()["error"]["code"] == "IDENTITY_NOT_LINKED"
    got = c.put("/api/approvals/identities", json={"slack": uid}, headers=H(a["token"])).json()["data"]
    assert got == {"slack": {"external_id": uid, "verified": False, "code_pending": False, "code_expires": None}, "telegram": None}
    # no channel that could DM the account yet
    assert c.post("/api/approvals/identities/slack/send-code", headers=H(a["token"])).json()["error"]["code"] == "CHANNEL_NOT_FOUND"
    c.put("/api/approvals/channels/slack", json=SLACK, headers=H(a["token"]))
    sent = c.post("/api/approvals/identities/slack/send-code", headers=H(a["token"])).json()["data"]["slack"]
    assert sent["code_pending"] and not sent["verified"] and api.named("chat.postMessage")[-1]["channel"] == uid 
    code = code_for(api, uid); assert code not in json.dumps(sent)
    r = c.post("/api/approvals/identities/slack/send-code", headers=H(a["token"]))  # resend throttle
    assert r.status_code == 429 and r.json()["error"]["code"] == "RATE_LIMITED" and int(r.headers["Retry-After"]) > 0
    wrong = "000000" if code != "000000" else "111111"
    r = c.post("/api/approvals/identities/slack/verify", json={"code": wrong}, headers=H(a["token"]))
    assert r.status_code == 400 and r.json()["error"] == {"code": "IDENTITY_CODE_INVALID", "message": "Wrong code, 4 attempt(s) left", "details": {"left": 4}}
    for _ in range(3): c.post("/api/approvals/identities/slack/verify", json={"code": wrong}, headers=H(a["token"]))
    r = c.post("/api/approvals/identities/slack/verify", json={"code": wrong}, headers=H(a["token"]))
    assert r.status_code == 429 and r.json()["error"]["code"] == "IDENTITY_CODE_ATTEMPTS"
    assert c.post("/api/approvals/identities/slack/verify", json={"code": code}, headers=H(a["token"])).json()["error"]["code"] == "IDENTITY_CODE_ATTEMPTS"
    monkeypatch.setenv("STUDIO_IDENTITY_CODE_RESEND", "0")
    c.post("/api/approvals/identities/slack/send-code", headers=H(a["token"])); code = code_for(api, uid)
    import app.services.identity_service as mod
    from types import SimpleNamespace
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(mod, "time", SimpleNamespace(time=lambda: time.time() + 3600))
        assert c.post("/api/approvals/identities/slack/verify", json={"code": code}, headers=H(a["token"])).status_code == 410  # IDENTITY_CODE_EXPIRED
    c.post("/api/approvals/identities/slack/send-code", headers=H(a["token"])); code = code_for(api, uid)
    assert c.post("/api/approvals/identities/slack/verify", json={"code": code}, headers=H(a["token"])).json()["data"]["slack"]["verified"] is True
    # b claims the same account: may link (unverified) but cannot verify it while a holds it
    c.put("/api/approvals/channels/slack", json=SLACK, headers=H(b["token"]))
    c.put("/api/approvals/identities", json={"slack": uid}, headers=H(b["token"])); c.post("/api/approvals/identities/slack/send-code", headers=H(b["token"]))
    r = c.post("/api/approvals/identities/slack/verify", json={"code": code_for(api, uid)}, headers=H(b["token"]))
    assert r.status_code == 409 and r.json()["error"]["code"] == "IDENTITY_TAKEN"
    assert c.put("/api/approvals/identities", json={"slack": ""}, headers=H(a["token"])).json()["data"]["slack"] is None  # unlink
    link(c, api, b, "slack", uid, own_channel=False)


def test_slack_approval_end_to_end(c, api):
    owner, approver, stranger = user(c), user(c), user(c)
    ch = c.put("/api/approvals/channels/slack", json=SLACK, headers=H(owner["token"])).json()["data"]
    ua, us = f"U{uuid.uuid4().hex[:8].upper()}", f"U{uuid.uuid4().hex[:8].upper()}"
    link(c, api, approver, "slack", ua); link(c, api, stranger, "slack", us)
    wid = workflow(c, owner, {"channel": "slack", "target": "C0APPROVALS", "approvers": [approver["email"].upper()]})
    rid = start_waiting(c, owner, wid)
    post = until(lambda: api.requests())[0]
    assert post["channel"] == "C0APPROVALS" and "Approve refund for order A100?" in post["blocks"][0]["text"]["text"]
    approve, reject = (e["value"] for e in post["blocks"][1]["elements"])
    # unauthenticated / tampered / replayed-late requests
    assert slack_post(c, ch["id"], press(approve, ua), secret="0" * 32).status_code == 401
    r = slack_post(c, ch["id"], press(approve, ua), ts=time.time() - 600); assert r.status_code == 401 and r.json()["error"]["code"] == "CHANNEL_SIGNATURE_INVALID"
    assert slack_post(c, ch["id"], press(approve[:-2] + "xx", ua)).json()["data"] == {"outcome": "refused", "code": "APPROVAL_TOKEN_INVALID"}
    assert slack_post(c, ch["id"], press(approve.replace("a.", "r.", 1), ua)).json()["data"]["code"] == "APPROVAL_TOKEN_INVALID"  # decision is signed
    # not mapped / not allowed: refused, told privately, run still waiting
    unverified = user(c); c.put("/api/approvals/identities", json={"slack": "U0NOBODY"}, headers=H(unverified["token"]))  # linked, never verified
    assert slack_post(c, ch["id"], press(approve, "U0NOBODY")).json()["data"]["code"] == "APPROVAL_IDENTITY_UNKNOWN"
    assert slack_post(c, ch["id"], press(approve, us)).json()["data"]["code"] == "APPROVAL_FORBIDDEN"
    eph = [b for u, b in api.calls if u.startswith("https://hooks.slack.com/")]
    assert len(eph) == 4 and {e["response_type"] for e in eph} == {"ephemeral"} and "not allowed" in eph[-1]["text"] and "Link and verify your Slack account" in eph[-2]["text"]
    assert run_row(c, owner, wid, rid)["status"] == "waiting"
    # allowed approver: accepted, run resumes in the worker, message edited
    assert slack_post(c, ch["id"], press(approve, ua)).json()["data"] == {"outcome": "approved"}
    done = until(lambda: (r := run_row(c, owner, wid, rid))["status"] == "ok" and r)
    assert done["final_state"]["decision"] == "approved"
    resumed = next(e for e in done["events"] if e["type"] == "run_resumed")
    assert resumed["response"] == "approved" and resumed["by"] == {"channel": "slack", "user_id": approver["id"]}
    upd = api.named("chat.update")[-1]; assert upd["ts"] == post.get("ts", upd["ts"]) and approver["email"] in upd["text"] and "Approved" in upd["text"]
    # single use: the same (or the other) button is refused afterwards
    assert slack_post(c, ch["id"], press(approve, ua)).json()["data"]["code"] == "APPROVAL_ALREADY_DECIDED"
    assert slack_post(c, ch["id"], press(reject, ua, "reject")).json()["data"]["code"] == "APPROVAL_ALREADY_DECIDED"
    log = c.get("/api/approvals/audit", headers=H(owner["token"])).json()["data"]
    mine = [e for e in log if e["run_id"] == rid][::-1]
    assert [(e["action"], e["code"]) for e in mine] == [("requested", None), ("denied", "APPROVAL_IDENTITY_UNKNOWN"), ("denied", "APPROVAL_FORBIDDEN"),
                                                       ("approved", None), ("denied", "APPROVAL_ALREADY_DECIDED"), ("denied", "APPROVAL_ALREADY_DECIDED")]
    assert mine[3]["actor"] == approver["email"] and mine[3]["external_id"] == ua and mine[0]["workflow_name"].startswith("Refund")
    assert c.get("/api/approvals/audit", headers=H(approver["token"])).json()["data"] == []  # the owner's log only


def test_telegram_webhook_registration_reject_and_secret_header(c, api, monkeypatch):
    monkeypatch.setenv("STUDIO_PUBLIC_URL", "https://studio.example.com")
    owner = user(c); tid = str(int(time.time() * 1000) % 10**12)
    ch = c.put("/api/approvals/channels/telegram", json=TG, headers=H(owner["token"])).json()["data"]
    assert ch["callback_url"] == f"https://studio.example.com/api/approvals/callback/telegram/{ch['id']}"
    reg = c.post("/api/approvals/channels/telegram/register-webhook", headers=H(owner["token"])).json()["data"]
    assert reg["registered"] is True and api.named("setWebhook")[-1] == {"url": ch["callback_url"], "secret_token": TG["webhook_secret"], "allowed_updates": ["callback_query"]}
    link(c, api, owner, "telegram", tid, own_channel=False)
    wid = workflow(c, owner, {"channel": "telegram", "target": "-100200300"}); rid = start_waiting(c, owner, wid)
    msg = until(lambda: api.requests("sendMessage"))[-1]
    keys = msg["reply_markup"]["inline_keyboard"][0]; reject = keys[1]["callback_data"]
    assert all(len(k["callback_data"].encode()) <= 64 for k in keys)  # Telegram's callback_data limit
    assert f"studio.example.com/workflows/{wid}?run={rid}" in msg["text"]
    upd = {"update_id": 1, "callback_query": {"id": "cq1", "from": {"id": int(tid)}, "data": reject, "message": {"message_id": 1, "chat": {"id": -100200300}}}}
    url = f"/api/approvals/callback/telegram/{ch['id']}"
    assert c.post(url, json=upd, headers={"X-Telegram-Bot-Api-Secret-Token": "wrong"}).status_code == 401
    assert c.post(url, json={"update_id": 2, "message": {"text": "hi"}}, headers={"X-Telegram-Bot-Api-Secret-Token": TG["webhook_secret"]}).json()["data"] == {"outcome": "ignored"}
    assert c.post(url, json=upd, headers={"X-Telegram-Bot-Api-Secret-Token": TG["webhook_secret"]}).json()["data"] == {"outcome": "rejected"}
    done = until(lambda: (r := run_row(c, owner, wid, rid))["status"] == "ok" and r)
    assert done["final_state"]["decision"] == "rejected"
    assert api.named("answerCallbackQuery")[-1]["show_alert"] is False and "Rejected" in api.named("editMessageText")[-1]["text"]


def test_expired_button_and_answer_in_studio_supersede(c, api):
    owner = user(c); ua = f"U{uuid.uuid4().hex[:8].upper()}"
    ch = c.put("/api/approvals/channels/slack", json=SLACK, headers=H(owner["token"])).json()["data"]
    link(c, api, owner, "slack", ua, own_channel=False)
    wid = workflow(c, owner, {"channel": "slack", "target": "C1"})
    # (1) expired token
    rid = start_waiting(c, owner, wid); approve = until(lambda: api.requests())[-1]["blocks"][1]["elements"][0]["value"]
    svc = approval_service(); req = svc.repo.requests_for_run(rid)[0]
    from sqlalchemy import update
    from app.models import ApprovalRequest
    with svc.repo.db.session() as s: s.execute(update(ApprovalRequest).where(ApprovalRequest.id == req.id).values(expires=time.time() - 1)); s.commit()
    assert slack_post(c, ch["id"], press(approve, ua)).json()["data"]["code"] == "APPROVAL_TOKEN_INVALID"  # expiry is signed into the token
    with svc.repo.db.session() as s: s.execute(update(ApprovalRequest).where(ApprovalRequest.id == req.id).values(expires=req.expires)); s.commit()
    import app.services.approval_service as mod
    from types import SimpleNamespace
    later = SimpleNamespace(time=lambda: req.expires + 1, strftime=time.strftime, gmtime=time.gmtime)
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(mod, "time", later)  # the service's clock only; the Slack signature check keeps real time
        assert slack_post(c, ch["id"], press(approve, ua)).json()["data"]["code"] == "APPROVAL_TOKEN_EXPIRED"
    assert svc.repo.request(req.id).status == "expired"
    # (2) answered in the studio: the channel request is closed and its message edited
    rid2 = start_waiting(c, owner, wid); approve2 = until(lambda: len(api.requests()) >= 2 and api.requests())[-1]["blocks"][1]["elements"][0]["value"]
    with c.websocket_connect(f"/ws/run?token={owner['token']}") as w:
        w.send_json({"resume_run_id": rid2, "response": True})
        while w.receive_json()["type"] != "run_summary": pass
    assert until(lambda: any(b["text"] == "Answered in LangGraph Studio" for b in api.named("chat.update")))
    assert slack_post(c, ch["id"], press(approve2, ua)).json()["data"]["code"] == "APPROVAL_ALREADY_DECIDED"
    actions = [e["action"] for e in c.get("/api/approvals/audit", headers=H(owner["token"])).json()["data"] if e["run_id"] == rid2]
    assert "superseded" in actions


def test_no_op_without_a_configured_channel(c, api):
    owner = user(c)
    wid = workflow(c, owner, {"channel": "slack", "target": "C1"}); rid = start_waiting(c, owner, wid)
    log = until(lambda: c.get("/api/approvals/audit", headers=H(owner["token"])).json()["data"])
    assert [(e["action"], e["code"], e["run_id"]) for e in log] == [("not_configured", "CHANNEL_NOT_FOUND", rid)] and api.calls == []
    wid2 = workflow(c, owner, {}); start_waiting(c, owner, wid2); time.sleep(0.2)
    assert len(c.get("/api/approvals/audit", headers=H(owner["token"])).json()["data"]) == 1  # no channel on the node: nothing at all


def test_send_failure_is_audited_and_the_run_keeps_waiting(c, api):
    owner = user(c); c.put("/api/approvals/channels/slack", json=SLACK, headers=H(owner["token"]))
    wid = workflow(c, owner, {"channel": "slack", "target": "C0FAIL"})
    orig = api.__call__
    rid = None
    def failing(req):
        if req.url.path.endswith("chat.postMessage"): return httpx.Response(200, json={"ok": False, "error": "channel_not_found"})
        return orig(req)
    for a in ADAPTERS.values(): a.transport = httpx.MockTransport(failing)
    rid = start_waiting(c, owner, wid)
    log = until(lambda: [e for e in c.get("/api/approvals/audit", headers=H(owner["token"])).json()["data"] if e["action"] == "send_failed"])
    assert log[0]["code"] == "CHANNEL_API_FAILED" and log[0]["run_id"] == rid
    assert run_row(c, owner, wid, rid)["status"] == "waiting"
