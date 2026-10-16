import asyncio, json, os, re, sqlite3, time, uuid, threading
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, UploadFile, File, Form
from typing import Optional
from . import importer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .compiler import validate, run_stream, TOOLS, ValidationError
from .example import EXAMPLE
from .auth import hash_password, verify_password, make_token, decode_token, current_user, password_problem, check_secret

DB = os.environ.get("STUDIO_DB", os.path.join(os.path.dirname(__file__), "..", "studio.db"))
app = FastAPI(title="LangGraph Studio MVP")
check_secret()
NAME_MAX = 120

def clean_name(name) -> str:
    n = " ".join(str(name or "").split())
    if not n: raise HTTPException(400, "Tên workflow không được để trống")
    if len(n) > NAME_MAX: raise HTTPException(400, f"Tên workflow tối đa {NAME_MAX} ký tự")
    return n

def unique_name(c, owner, base, exclude=None) -> str:
    """'X' -> 'X (copy)' -> 'X (copy 2)'... unique among the owner's workflows."""
    names = {r["name"] for r in c.execute("SELECT id, name FROM workflows WHERE owner=?", (owner,)) if r["id"] != exclude}
    if base not in names: return base
    root = re.sub(r" \(copy(?: \d+)?\)$", "", base)
    def mk(suffix): return f"{root[:NAME_MAX - len(suffix)].rstrip()}{suffix}"
    n, cand = 1, mk(" (copy)")
    while cand in names: n += 1; cand = mk(f" (copy {n})")
    return cand
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
DEMO_EMAIL, DEMO_PW = "admin@example.com", "admin123"

def db():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c

def seed_example(c, owner, wid=None):
    wid = wid or uuid.uuid4().hex[:8]
    c.execute("INSERT INTO workflows(id,name,data,updated,owner) VALUES(?,?,?,?,?)",
              (wid, EXAMPLE["name"], json.dumps(EXAMPLE, ensure_ascii=False), time.time(), owner))
    return wid

def init_db():
    with db() as c:
        c.execute("CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, email TEXT UNIQUE, password TEXT, created REAL)")
        c.execute("CREATE TABLE IF NOT EXISTS workflows(id TEXT PRIMARY KEY, name TEXT, data TEXT, updated REAL, owner TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, workflow_id TEXT, input TEXT, events TEXT, final_state TEXT, status TEXT, started REAL, ended REAL)")
        cols = [r[1] for r in c.execute("PRAGMA table_info(workflows)")]
        if "owner" not in cols: c.execute("ALTER TABLE workflows ADD COLUMN owner TEXT")
        u = c.execute("SELECT id FROM users WHERE email=?", (DEMO_EMAIL,)).fetchone()
        uid = u["id"] if u else "admin"
        if not u:
            c.execute("INSERT INTO users VALUES(?,?,?,?)", (uid, DEMO_EMAIL, hash_password(DEMO_PW), time.time()))
        c.execute("UPDATE workflows SET owner=? WHERE owner IS NULL", (uid,))
        if not c.execute("SELECT 1 FROM workflows WHERE id='example'").fetchone():
            seed_example(c, uid, "example")
init_db()

class Creds(BaseModel):
    email: str
    password: str

@app.post("/api/auth/register")
def register(cr: Creds):
    email = cr.email.strip().lower()
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email): raise HTTPException(400, "Email không hợp lệ")
    if len(email) > 254: raise HTTPException(400, "Email không hợp lệ")
    if (msg := password_problem(cr.password)): raise HTTPException(400, msg)
    uid = uuid.uuid4().hex[:10]
    with db() as c:
        if c.execute("SELECT 1 FROM users WHERE email=?", (email,)).fetchone(): raise HTTPException(409, "Email đã được đăng ký")
        c.execute("INSERT INTO users VALUES(?,?,?,?)", (uid, email, hash_password(cr.password), time.time()))
        seed_example(c, uid)
    return {"token": make_token(uid, email), "user": {"id": uid, "email": email}}

@app.post("/api/auth/login")
def login(cr: Creds):
    email = cr.email.strip().lower()
    with db() as c:
        u = c.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    if not u or not verify_password(cr.password, u["password"]):
        raise HTTPException(401, "Sai email hoặc mật khẩu")  # generic: no user enumeration
    return {"token": make_token(u["id"], email), "user": {"id": u["id"], "email": email}}

@app.get("/api/me")
def me(user=Depends(current_user)): return user

@app.get("/api/health")
def health(): return {"ok": True, "llm_mode": "openai" if os.environ.get("OPENAI_API_KEY") else "mock"}

@app.get("/api/tools")
def tools(user=Depends(current_user)): return [{"name": k, "doc": (v.__doc__ or "").strip()} for k, v in TOOLS.items()]

def _own(c, wid, uid):
    r = c.execute("SELECT * FROM workflows WHERE id=? AND owner=?", (wid, uid)).fetchone()
    if not r: raise HTTPException(404, "Không tìm thấy workflow")
    return r

@app.get("/api/workflows")
def list_wf(user=Depends(current_user)):
    out = []
    with db() as c:
        for r in c.execute("SELECT * FROM workflows WHERE owner=? ORDER BY updated DESC", (user["id"],)):
            last = c.execute("SELECT status, started FROM runs WHERE workflow_id=? ORDER BY started DESC LIMIT 1", (r["id"],)).fetchone()
            d = json.loads(r["data"])
            out.append({"id": r["id"], "name": r["name"], "updated": r["updated"], "node_count": len(d.get("nodes", [])),
                        "last_run_status": last["status"] if last else None, "last_run_at": last["started"] if last else None})
    return out

@app.get("/api/workflows/{wid}")
def get_wf(wid: str, user=Depends(current_user)):
    with db() as c: r = _own(c, wid, user["id"])
    return {"id": r["id"], **json.loads(r["data"])}

@app.post("/api/workflows")
def save_wf(wf: dict, user=Depends(current_user)):
    wid = wf.get("id") or uuid.uuid4().hex[:8]
    wf = {k: v for k, v in wf.items() if k != "id"}
    with db() as c:
        ex = c.execute("SELECT owner FROM workflows WHERE id=?", (wid,)).fetchone()
        if ex and ex["owner"] != user["id"]: raise HTTPException(403, "Không có quyền")
        old = json.loads(c.execute("SELECT data FROM workflows WHERE id=?", (wid,)).fetchone()["data"]) if ex else {}
        wf["name"] = clean_name(wf.get("name", "Untitled workflow"))
        if not ex: wf["name"] = unique_name(c, user["id"], wf["name"])
        wf.pop("source", None)  # never trust client-provided source metadata
        if old.get("source"): wf["source"] = old["source"]
        c.execute("INSERT OR REPLACE INTO workflows(id,name,data,updated,owner) VALUES(?,?,?,?,?)",
                  (wid, wf.get("name", "Untitled"), json.dumps(wf, ensure_ascii=False), time.time(), user["id"]))
    return {"id": wid, "errors": [] if wf.get("source") else validate(wf)}

class Rename(BaseModel):
    name: str

@app.patch("/api/workflows/{wid}")
def rename_wf(wid: str, body: Rename, user=Depends(current_user)):
    with db() as c:
        r = _own(c, wid, user["id"]); name = clean_name(body.name)
        if any(x["name"] == name for x in c.execute("SELECT name FROM workflows WHERE owner=? AND id!=?", (user["id"], wid))):
            raise HTTPException(409, "Đã có workflow trùng tên")
        d = json.loads(r["data"]); d["name"] = name
        c.execute("UPDATE workflows SET name=?, data=?, updated=? WHERE id=?", (name, json.dumps(d, ensure_ascii=False), time.time(), wid))
    return {"ok": True, "name": name}

@app.post("/api/workflows/{wid}/duplicate")
def dup_wf(wid: str, user=Depends(current_user)):
    nid = uuid.uuid4().hex[:8]
    with db() as c:
        r = _own(c, wid, user["id"]); d = json.loads(r["data"]); d["name"] = unique_name(c, user["id"], r["name"])
        c.execute("INSERT INTO workflows(id,name,data,updated,owner) VALUES(?,?,?,?,?)", (nid, d["name"], json.dumps(d, ensure_ascii=False), time.time(), user["id"]))
    return {"id": nid, "name": d["name"]}

@app.delete("/api/workflows/{wid}")
def del_wf(wid: str, user=Depends(current_user)):
    with db() as c:
        _own(c, wid, user["id"])
        c.execute("DELETE FROM workflows WHERE id=?", (wid,)); c.execute("DELETE FROM runs WHERE workflow_id=?", (wid,))
    return {"ok": True}

@app.post("/api/import")
async def import_repo(url: Optional[str] = Form(None), branch: Optional[str] = Form(None), subdir: Optional[str] = Form(None),
                      file: Optional[UploadFile] = File(None), user=Depends(current_user)):
    try:
        if file is not None:
            data = await file.read()
            if len(data) > 50 * 1024 * 1024: raise HTTPException(413, "Zip quá lớn (>50MB)")
            jid = importer.start_job(user["id"], "zip", branch=None, subdir=subdir or None, zip_bytes=data)
        elif url:
            jid = importer.start_job(user["id"], "url", url=url.strip(), branch=branch or None, subdir=subdir or None)
        else:
            raise HTTPException(400, "Cần url hoặc file zip")
    except importer.ImportError_ as e:
        raise HTTPException(400, str(e))
    return {"job_id": jid}

def _job(jid, user):
    j = importer.JOBS.get(jid)
    if not j or j["owner"] != user["id"]: raise HTTPException(404, "Không tìm thấy import job")
    return j

@app.get("/api/import/{jid}")
def import_status(jid: str, user=Depends(current_user)): return importer.public_job(_job(jid, user))

class Finalize(BaseModel):
    graph_id: str

@app.post("/api/import/{jid}/finalize")
def import_finalize(jid: str, body: Finalize, user=Depends(current_user)):
    j = _job(jid, user)
    if j["status"] != "ready" or body.graph_id not in [g["id"] for g in j["graphs"]]: raise HTTPException(400, "Job chưa sẵn sàng hoặc graph không hợp lệ")
    wf = importer.to_workflow(j, body.graph_id); wid = uuid.uuid4().hex[:8]
    with db() as c:
        c.execute("INSERT INTO workflows(id,name,data,updated,owner) VALUES(?,?,?,?,?)", (wid, wf["name"], json.dumps(wf, ensure_ascii=False), time.time(), user["id"]))
    return {"id": wid}

@app.post("/api/validate")
def validate_wf(wf: dict, user=Depends(current_user)): return {"errors": validate(wf)}

@app.get("/api/workflows/{wid}/runs")
def runs(wid: str, user=Depends(current_user)):
    with db() as c:
        _own(c, wid, user["id"])
        return [{**dict(r), "input": json.loads(r["input"]), "final_state": json.loads(r["final_state"] or "null"), "events": json.loads(r["events"])}
                for r in c.execute("SELECT * FROM runs WHERE workflow_id=? ORDER BY started DESC LIMIT 50", (wid,))]

@app.websocket("/ws/run")
async def ws_run(ws: WebSocket):
    """Connect with ?token=JWT. Client sends {workflow_id, workflow?, input}; server streams events."""
    tok = ws.query_params.get("token")
    try:
        p = decode_token(tok or ""); uid = p["sub"]
    except HTTPException:
        await ws.close(code=4401); return
    await ws.accept()
    try:
        req = await ws.receive_json()
        wid = req.get("workflow_id")
        if wid:
            with db() as c:
                r = c.execute("SELECT * FROM workflows WHERE id=? AND owner=?", (wid, uid)).fetchone()
            if not r:
                await ws.send_json({"type": "error", "errors": ["Không tìm thấy workflow"]}); await ws.close(); return
        inp = req.get("input", {})
        stored = json.loads(r["data"]) if wid else {}
        wf = stored if stored.get("source") else (req.get("workflow") or stored)
        gen = (lambda: importer.run_imported(wf, dict(inp))) if wf.get("source", {}).get("kind") == "langgraph_import" else (lambda: run_stream(wf, inp))
        rid = uuid.uuid4().hex[:10]; t0 = time.time(); events = []; final = None; status = "ok"
        q: asyncio.Queue = asyncio.Queue(); loop = asyncio.get_running_loop()
        def worker():
            try:
                for ev in gen(): loop.call_soon_threadsafe(q.put_nowait, ev)
            except ValidationError as e:
                loop.call_soon_threadsafe(q.put_nowait, {"type": "error", "errors": e.errors})
            except Exception as e:
                loop.call_soon_threadsafe(q.put_nowait, {"type": "error", "errors": [f"{type(e).__name__}: {e}"]})
            loop.call_soon_threadsafe(q.put_nowait, None)
        start_ev = {"type": "run_started", "run_id": rid, "ts": t0}; events.append(start_ev)
        await ws.send_json(start_ev)
        threading.Thread(target=worker, daemon=True).start()
        while (ev := await q.get()) is not None:
            ev["ts"] = time.time(); events.append(ev)
            if ev["type"] == "run_finished": final = ev["state"]
            if ev["type"] == "error": status = "error"
            await ws.send_json(ev)
        with db() as c:
            c.execute("INSERT INTO runs VALUES(?,?,?,?,?,?,?,?)", (rid, wid or "adhoc", json.dumps(inp, ensure_ascii=False),
                      json.dumps(events, ensure_ascii=False), json.dumps(final, ensure_ascii=False), status, t0, time.time()))
        await ws.close()
    except WebSocketDisconnect:
        pass
