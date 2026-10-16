import asyncio, json, os, re, sqlite3, time, uuid, threading
from fastapi import Request, FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, UploadFile, File, Form
from typing import Optional
from . import importer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from .compiler import validate, run_stream, TOOLS, ValidationError
from .example import EXAMPLE
from . import limits
from .limits import cap_event, cap_run, safe_error
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
    c = sqlite3.connect(DB, timeout=15); c.row_factory = sqlite3.Row; return c

def seed_example(c, owner, wid=None):
    wid = wid or uuid.uuid4().hex[:8]
    c.execute("INSERT INTO workflows(id,name,data,updated,owner) VALUES(?,?,?,?,?)",
              (wid, EXAMPLE["name"], json.dumps(EXAMPLE, ensure_ascii=False), time.time(), owner))
    return wid

def init_db():
    with db() as c:
        c.execute("PRAGMA journal_mode=WAL")
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

# ---------- request models & readable validation errors ----------
class NodeIn(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str = Field(min_length=1, max_length=64)
    type: str = Field(min_length=1, max_length=32)
    position: Optional[dict] = None
    data: dict = Field(default_factory=dict)

class EdgeIn(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str = Field(min_length=1, max_length=64)
    source: str = Field(min_length=1)
    target: str = Field(min_length=1)
    label: Optional[str] = None

class FieldIn(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str = Field(min_length=1, max_length=64)
    type: str = "string"

class WorkflowIn(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: Optional[str] = None
    name: Optional[str] = None
    state: list[FieldIn] = Field(default_factory=list, max_length=200)
    nodes: list[NodeIn] = Field(default_factory=list, max_length=500)
    edges: list[EdgeIn] = Field(default_factory=list, max_length=2000)

def _loc(err):
    return ".".join(str(x) for x in err.get("loc", []) if x != "body") or "body"

@app.exception_handler(RequestValidationError)
async def readable_422(request, exc: RequestValidationError):
    errs = [f"{_loc(e)}: {e.get('msg')}" for e in exc.errors()][:10]
    return JSONResponse(status_code=422, content={"detail": "Dữ liệu không hợp lệ — " + "; ".join(errs), "errors": errs})

async def _limit_body(request: Request):
    n = int(request.headers.get("content-length") or 0)
    if n > limits.workflow_max(): raise HTTPException(413, f"Workflow quá lớn (> {limits.workflow_max() // 1024} KB)")

def _wf_dict(m: WorkflowIn) -> dict:
    return m.model_dump(exclude_none=True)

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

@app.post("/api/workflows", dependencies=[Depends(_limit_body)])
def save_wf(body: WorkflowIn, user=Depends(current_user)):
    wf = _wf_dict(body)
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

@app.post("/api/validate", dependencies=[Depends(_limit_body)])
def validate_wf(body: WorkflowIn, user=Depends(current_user)): return {"errors": validate(_wf_dict(body))}

@app.get("/api/workflows/{wid}/runs")
def runs(wid: str, user=Depends(current_user)):
    with db() as c:
        _own(c, wid, user["id"])
        return [{**dict(r), "input": json.loads(r["input"]), "final_state": json.loads(r["final_state"] or "null"), "events": json.loads(r["events"])}
                for r in c.execute("SELECT * FROM runs WHERE workflow_id=? ORDER BY started DESC LIMIT 50", (wid,))]

def _save_run(rid, wid, inp, events, final, status, t0):
    events = cap_run([cap_event(e) for e in events])
    final = cap_event({"state": final})["state"] if final is not None else None
    with db() as c:
        c.execute("INSERT INTO runs VALUES(?,?,?,?,?,?,?,?)", (rid, wid or "adhoc", json.dumps(inp, ensure_ascii=False, default=str),
                  json.dumps(events, ensure_ascii=False, default=str), json.dumps(final, ensure_ascii=False, default=str), status, t0, time.time()))


@app.websocket("/ws/run")
async def ws_run(ws: WebSocket):
    """Connect with ?token=JWT. Client sends {workflow_id, workflow?, input}; server streams events.
    While running, the client may send {"type": "cancel"}; closing the socket also cancels.
    Final status: ok | error | cancelled | timeout (stored in run history)."""
    tok = ws.query_params.get("token")
    try:
        p = decode_token(tok or ""); uid = p["sub"]
    except HTTPException:
        await ws.close(code=4401); return
    await ws.accept()
    try:
        req = await ws.receive_json()
    except (WebSocketDisconnect, ValueError, KeyError):
        return
    if not isinstance(req, dict):
        await ws.send_json({"type": "error", "errors": ["Yêu cầu phải là JSON object"]}); await ws.close(); return
    wid = req.get("workflow_id"); r = None
    if wid:
        with db() as c:
            r = c.execute("SELECT * FROM workflows WHERE id=? AND owner=?", (wid, uid)).fetchone()
        if not r:
            await ws.send_json({"type": "error", "errors": ["Không tìm thấy workflow"]}); await ws.close(); return
    inp = req.get("input", {})
    if not isinstance(inp, dict) or limits.size(inp) > limits.input_max():
        msg = "Input phải là một JSON object" if not isinstance(inp, dict) else f"Input quá lớn (> {limits.input_max() // 1024} KB)"
        await ws.send_json({"type": "error", "errors": [msg]}); await ws.close(); return
    stored = json.loads(r["data"]) if r else {}
    wf = stored if stored.get("source") else (req.get("workflow") or stored)
    if not isinstance(wf, dict) or limits.size(wf) > limits.workflow_max():
        await ws.send_json({"type": "error", "errors": ["Workflow không hợp lệ hoặc quá lớn"]}); await ws.close(); return
    imported = (wf.get("source") or {}).get("kind") == "langgraph_import"
    gen = (lambda: importer.run_imported(wf, dict(inp))) if imported else (lambda: run_stream(wf, inp))
    rid = uuid.uuid4().hex[:10]; t0 = time.time(); events = []; final = None; status = "ok"
    q: asyncio.Queue = asyncio.Queue(); loop = asyncio.get_running_loop(); cancel = threading.Event()

    def put(x):
        try: loop.call_soon_threadsafe(q.put_nowait, x)
        except RuntimeError: pass  # loop closed after client went away

    def worker():
        g = None
        try:
            g = gen()
            for ev in g:
                if cancel.is_set(): break  # cooperative cancel between steps
                put(ev)
        except ValidationError as e:
            put({"type": "error", "errors": e.errors})
        except Exception as e:
            put({"type": "error", "errors": [safe_error(e)]})
        finally:
            if g is not None:
                try: g.close()  # stops LangGraph stream / kills import subprocess
                except Exception: pass
            put(None)

    async def listen():
        try:
            while True:
                m = await ws.receive_json()
                if isinstance(m, dict) and m.get("type") == "cancel": return "cancelled"
        except (WebSocketDisconnect, RuntimeError, ValueError):
            return "disconnected"

    async def send(ev):
        nonlocal connected
        if not connected: return
        try: await ws.send_json(cap_event(ev))
        except Exception: connected = False

    connected = True
    start_ev = {"type": "run_started", "run_id": rid, "ts": t0}; events.append(start_ev)
    await send(start_ev)
    threading.Thread(target=worker, daemon=True).start()
    listener = asyncio.create_task(listen()); deadline = t0 + limits.run_timeout(); ended = None
    while True:
        get = asyncio.ensure_future(q.get())
        done, _ = await asyncio.wait({get, listener}, timeout=max(0.0, deadline - time.time()), return_when=asyncio.FIRST_COMPLETED)
        if get in done:
            ev = get.result()
            if ev is None: break
            ev["ts"] = time.time(); events.append(ev)
            if ev["type"] == "run_finished": final = ev.get("state")
            if ev["type"] == "error": status = "error"
            await send(ev); continue
        get.cancel()
        if listener in done:
            ended = listener.result(); connected = connected and ended == "cancelled"
        else:
            ended = "timeout"
        cancel.set(); break
    if not listener.done(): listener.cancel()
    if ended in ("cancelled", "disconnected"):
        status = "cancelled"
        ev = {"type": "run_cancelled", "ts": time.time(), "reason": "client" if ended == "cancelled" else "disconnect"}
        events.append(ev); await send(ev)
    elif ended == "timeout":
        status = "timeout"
        ev = {"type": "error", "status": "timeout", "ts": time.time(),
              "errors": [f"Run vượt quá thời gian cho phép ({limits.run_timeout():g}s, STUDIO_RUN_TIMEOUT)"]}
        events.append(ev); await send(ev)
    await asyncio.to_thread(_save_run, rid, wid, inp, events, final, status, t0)
    if connected:
        try: await ws.close()
        except Exception: pass
