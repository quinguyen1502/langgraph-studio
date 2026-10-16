import json, threading, time, uuid
import pytest
from fastapi.testclient import TestClient
from app import limits
from app.compiler import validate, run_stream, register_tool, TOOLS, check_input
from app.example import EXAMPLE
from app.limits import cap_event, cap_run, safe_error
from app.main import app

c = TestClient(app)
def H(t): return {"Authorization": f"Bearer {t}"}
def token(): return c.post("/api/auth/login", json={"email": "admin@example.com", "password": "admin123"}).json()["token"]
def N(i, t, **d): return {"id": i, "type": t, "data": {"label": i, **d}}
def E(i, s, t, label=None): return {"id": i, "source": s, "target": t, **({"label": label} if label else {})}
def wf(nodes, edges, state=("message", "intent", "out")): return {"name": "t", "state": [{"name": s, "type": "string"} for s in state], "nodes": nodes, "edges": edges}
LINEAR = wf([N("s", "start"), N("l", "llm", prompt="{{state.message}}", output_field="out"), N("e", "end")], [E("1", "s", "l"), E("2", "l", "e")])

@register_tool("sleep_1s")
def _sleep(state):
    """test helper: sleeps 1s"""
    time.sleep(1); return "slept"

# ---------- validation ----------
def has(errs, frag): return any(frag in e for e in errs), errs

def test_valid_baseline():
    assert validate(LINEAR) == [] and validate(EXAMPLE) == []

@pytest.mark.parametrize("mutate,frag", [
    (lambda w: w["edges"].append(E("x", "l", "ghost")), "không tồn tại: ghost"),
    (lambda w: w["nodes"].append(N("l", "end")), "Trùng id node: l"),
    (lambda w: w["edges"].append(E("1", "s", "e")), "Trùng id edge: 1"),
    (lambda w: w["nodes"].append(N("s2", "start")) or w["edges"].append(E("9", "s2", "l")), "Chỉ được 1 node Start"),
    (lambda w: w["nodes"].pop(0) and w["edges"].pop(0), "chưa có"),
    (lambda w: w["edges"].append(E("x", "l", "l")), "tự nối"),
    (lambda w: w["nodes"].append(N("orphan", "llm", prompt="", output_field="out")) or w["edges"].append(E("o", "orphan", "e")), "không đi tới được"),
    (lambda w: w.update(nodes=[{"type": "start"}]), "cần có id"),
])
def test_validation_rejections(mutate, frag):
    w = json.loads(json.dumps(LINEAR)); mutate(w)
    ok, errs = has(validate(w), frag); assert ok, errs

def test_cycle_without_condition_rejected_but_through_condition_ok():
    a = N("a", "llm", prompt="x", output_field="out"); b = N("b", "llm", prompt="x", output_field="out")
    bad = wf([N("s", "start"), a, b, N("e", "end")], [E("1", "s", "a"), E("2", "a", "b"), E("3", "b", "a")])
    assert has(validate(bad), "Vòng lặp không qua Condition: a → b → a")[0]
    good = wf([N("s", "start"), a, N("c", "condition", field="intent", default="again"), N("e", "end")],
              [E("1", "s", "a"), E("2", "a", "c"), E("3", "c", "a", "again"), E("4", "c", "e", "done")])
    assert validate(good) == []

# ---------- condition routing ----------
def cond_wf(default=""):
    return wf([N("s", "start"), N("c", "condition", label="Router", field="intent", default=default), N("x", "end"), N("y", "end")],
              [E("1", "s", "c"), E("2", "c", "x", "yes"), E("3", "c", "y", "no")])

def test_condition_default_and_no_match():
    evs = list(run_stream(cond_wf("no"), {"intent": "maybe"}))
    assert evs[-1]["type"] == "run_finished" and any(e["type"] == "node_finished" and e["node"] == "y" for e in evs)
    evs = list(run_stream(cond_wf(), {"intent": "maybe"}))
    err = evs[-1]; assert err["type"] == "error" and err["node"] == "c"
    assert "Router" in err["errors"][0] and "intent='maybe'" in err["errors"][0] and "Traceback" not in err["errors"][0]

@pytest.mark.parametrize("val,target", [(" YES ", "x"), (True, None), (None, None), (0, None)])
def test_condition_value_normalisation(val, target):
    w = cond_wf("no"); w["state"] = [{"name": "intent", "type": "any"}]  # untyped field: any JSON value
    evs = list(run_stream(w, {"intent": val}))
    reached = [e["node"] for e in evs if e["type"] == "node_finished" and e["node"] in ("x", "y")]
    assert reached == [target or "y"]

# ---------- state edge cases ----------
def test_empty_state_schema_and_missing_fields():
    w = wf([N("s", "start"), N("e", "end")], [E("1", "s", "e")], state=())
    assert list(run_stream(w, {}))[-1]["type"] == "run_finished"
    assert list(run_stream(LINEAR, {}))[-1]["type"] == "run_finished"  # message missing -> empty render

def test_input_type_mismatch():
    w = dict(LINEAR, state=[{"name": "message", "type": "string"}, {"name": "n", "type": "number"}, {"name": "out", "type": "string"}])
    assert check_input(w, {"n": "abc"}) == ["Input 'n' phải có kiểu number (nhận str)"]
    assert check_input(w, {"n": True}) and check_input(w, [1]) and check_input(w, {"n": 2.5}) == []

# ---------- caps & sanitising ----------
def test_cap_event_and_run():
    big = {"type": "run_finished", "state": {"x": "y" * 400_000}}
    capped = cap_event(big)
    assert limits.size(capped) <= limits.event_max() and capped["state"]["_truncated"] and capped["_truncated"]
    small = {"type": "node_started", "node": "a"}; assert cap_event(small) is small
    evs = [{"type": "node_finished", "node": str(i), "delta": "z" * 10_000} for i in range(400)]
    kept = cap_run(evs)
    assert limits.size(kept) <= limits.run_max() and any(e["type"] == "truncated" for e in kept)
    assert kept[0]["node"] == "0" and kept[-1]["node"] == "399"
    assert cap_run(evs[:3]) == evs[:3]

def test_safe_error_redacts_and_no_traceback():
    m = safe_error(RuntimeError("bad key sk-abcdef1234567890 Bearer xyz.123 url?api_key=SECRET&x=1\nTraceback line"))
    assert "sk-abcdef" not in m and "xyz.123" not in m and "SECRET" not in m and "Traceback" not in m
    assert len(safe_error(ValueError("x" * 2000))) <= 501

# ---------- websocket lifecycle ----------
def slow_wf(n=3):
    nodes = [N("s", "start")] + [N(f"t{i}", "tool", mode="function", function="sleep_1s", output_field="out") for i in range(n)] + [N("e", "end")]
    ids = ["s"] + [f"t{i}" for i in range(n)] + ["e"]
    return wf(nodes, [E(str(i), a, b) for i, (a, b) in enumerate(zip(ids, ids[1:]))])

def last_run(t, wid):
    return c.get(f"/api/workflows/{wid}/runs", headers=H(t)).json()[0]

def save(t, w): return c.post("/api/workflows", json=w, headers=H(t)).json()["id"]

def test_cancel_message_stops_run():
    t = token(); wid = save(t, slow_wf(5)); t0 = time.time()
    with c.websocket_connect(f"/ws/run?token={t}") as ws:
        ws.send_json({"workflow_id": wid, "input": {}})
        assert ws.receive_json()["type"] == "run_started"
        ws.send_json({"type": "cancel"})
        evs = []
        while True:
            e = ws.receive_json(); evs.append(e)
            if e["type"] == "run_cancelled": break
    assert time.time() - t0 < 3
    time.sleep(0.3); assert last_run(t, wid)["status"] == "cancelled"

def test_disconnect_cancels_run():
    t = token(); wid = save(t, slow_wf(5))
    with c.websocket_connect(f"/ws/run?token={t}") as ws:
        ws.send_json({"workflow_id": wid, "input": {}}); ws.receive_json()
    for _ in range(40):
        time.sleep(0.1)
        runs = c.get(f"/api/workflows/{wid}/runs", headers=H(t)).json()
        if runs: break
    assert runs and runs[0]["status"] == "cancelled" and runs[0]["events"][-1]["reason"] == "disconnect"

def test_timeout(monkeypatch):
    monkeypatch.setenv("STUDIO_RUN_TIMEOUT", "1.2")
    t = token(); wid = save(t, slow_wf(4))
    with c.websocket_connect(f"/ws/run?token={t}") as ws:
        ws.send_json({"workflow_id": wid, "input": {}})
        while (e := ws.receive_json())["type"] != "error": pass
    assert e["status"] == "timeout" and "STUDIO_RUN_TIMEOUT" in e["errors"][0]
    time.sleep(0.3); assert last_run(t, wid)["status"] == "timeout"

def test_bad_run_input_over_ws():
    t = token()
    for inp, frag in [([1, 2], "JSON object"), ({"x": "y" * (300 * 1024)}, "quá lớn")]:
        with c.websocket_connect(f"/ws/run?token={t}") as ws:
            ws.send_json({"workflow": LINEAR, "input": inp}); e = ws.receive_json()
        assert e["type"] == "error" and frag in e["errors"][0]

def test_five_concurrent_runs_isolated():
    t = token(); results = {}
    def one(i):
        cl = TestClient(app)
        with cl.websocket_connect(f"/ws/run?token={t}") as ws:
            ws.send_json({"workflow": LINEAR, "input": {"message": f"msg-{i}"}})
            evs = []
            while True:
                try: e = ws.receive_json()
                except Exception: break
                evs.append(e)
                if e["type"] in ("run_finished", "error"): break
        results[i] = evs
    th = [threading.Thread(target=one, args=(i,)) for i in range(6)]
    [x.start() for x in th]; [x.join(30) for x in th]
    assert len(results) == 6
    for i, evs in results.items():
        assert evs[-1]["type"] == "run_finished", evs[-1]
        assert evs[-1]["state"]["message"] == f"msg-{i}" and f"msg-{i}" in evs[-1]["state"]["out"]
        assert len({e["run_id"] for e in evs if e["type"] == "run_started"}) == 1

# ---------- HTTP input validation ----------
def test_readable_422_and_413():
    t = token()
    r = c.post("/api/workflows", json={"name": "x", "nodes": [{"id": "", "type": "start"}], "edges": "nope"}, headers=H(t))
    assert r.status_code == 422 and r.json()["detail"].startswith("Dữ liệu không hợp lệ") and "nodes.0.id" in r.json()["detail"] and "edges" in r.json()["detail"]
    r = c.post("/api/workflows", content=b"[1,2]", headers={**H(t), "Content-Type": "application/json"}); assert r.status_code == 422
    big = {"name": "big", "nodes": [], "edges": [], "blob": "x" * (1100 * 1024)}
    r = c.post("/api/workflows", json=big, headers=H(t)); assert r.status_code == 413 and "quá lớn" in r.json()["detail"]
    assert c.post("/api/validate", json={"nodes": [{"id": "a"}]}, headers=H(t)).status_code == 422
