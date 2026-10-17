"""Import LangGraph repos: clone/unzip -> per-import venv -> inspect graphs in subprocess -> workflow JSON.
SECURITY: imported code is arbitrary. It is only ever executed in a subprocess using the import's own venv,
with a reduced environment and a timeout. It is NOT sandboxed beyond that (same OS user, network access)."""
from __future__ import annotations
import json, os, re, shutil, subprocess, sys, threading, time, uuid, zipfile
from typing import Any, Dict, List, Optional

# Import workspaces live OUTSIDE the repository by default (keeps cloned repos/venvs out of git and tooling scans).
# Override with STUDIO_IMPORT_DIR. Workflows imported earlier keep their absolute paths and still run.
ROOT = os.path.expanduser(os.environ.get("STUDIO_IMPORT_DIR") or "~/.langgraph-studio/imports")
RUNNER = os.path.join(os.path.dirname(__file__), "sandbox", "runner.py")
INSPECT_TIMEOUT = int(os.environ.get("STUDIO_INSPECT_TIMEOUT", "120"))
RUN_TIMEOUT = int(os.environ.get("STUDIO_RUN_TIMEOUT", "300"))
INSTALL_TIMEOUT = 900
GH_RE = re.compile(r"^https://github\.com/[\w.-]+/[\w.-]+?(\.git)?/?$")
JOBS: Dict[str, Dict[str, Any]] = {}


def sub_env() -> Dict[str, str]:
    keep = {"PATH", "HOME", "LANG", "LC_ALL", "TMPDIR", "UV_CACHE_DIR"}
    env = {k: v for k, v in os.environ.items() if k in keep or k.endswith("_API_KEY") or k.startswith(("LANGSMITH_", "LANGCHAIN_", "OPENAI_"))}
    env.pop("JWT_SECRET", None); env["PYTHONUNBUFFERED"] = "1"; env["GIT_TERMINAL_PROMPT"] = "0"
    return env


class ImportError_(Exception):
    pass


def _log(job, msg):
    job["log"].append(f"[{time.strftime('%H:%M:%S')}] {msg}")


def _sh(job, cmd, cwd=None, timeout=INSTALL_TIMEOUT):
    _log(job, "$ " + " ".join(cmd))
    p = subprocess.run(cmd, cwd=cwd, env=sub_env(), capture_output=True, text=True, timeout=timeout)
    tail = (p.stdout + p.stderr).strip().splitlines()[-15:]
    for l in tail: job["log"].append("  " + l)
    if p.returncode != 0: raise ImportError_(f"Command failed ({p.returncode}): {' '.join(cmd[:3])}…")


def safe_extract(zpath: str, dest: str) -> str:
    with zipfile.ZipFile(zpath) as z:
        for m in z.infolist():
            target = os.path.realpath(os.path.join(dest, m.filename))
            if not target.startswith(os.path.realpath(dest) + os.sep) and target != os.path.realpath(dest):
                raise ImportError_(f"Zip contains an unsafe path: {m.filename}")
        z.extractall(dest)
    entries = [e for e in os.listdir(dest) if not e.startswith("__MACOSX")]
    return os.path.join(dest, entries[0]) if len(entries) == 1 and os.path.isdir(os.path.join(dest, entries[0])) else dest


def find_graphs(repo: str) -> List[Dict[str, str]]:
    lj = os.path.join(repo, "langgraph.json")
    if os.path.exists(lj):
        graphs = json.load(open(lj)).get("graphs", {})
        out = []
        for gid, ref in graphs.items():
            ref = ref if isinstance(ref, str) else ref.get("path", "")
            if ":" in ref: out.append({"id": gid, "ref": ref.removeprefix("./"), "via": "langgraph.json"})
        if out: return out
    out = []
    pat = re.compile(r"^(\w+)\s*(?::[^=]+)?=\s*[^\n#]*\.compile\(", re.M)
    for dp, dns, fns in os.walk(repo):
        dns[:] = [d for d in dns if d not in (".git", ".venv", "venv", "node_modules", "tests", "test", "__pycache__")]
        for f in fns:
            if f.endswith(".py"):
                p = os.path.join(dp, f)
                try: src = open(p, encoding="utf-8", errors="ignore").read()
                except Exception: continue
                if "StateGraph" not in src: continue
                for m in pat.finditer(src):
                    rel = os.path.relpath(p, repo)
                    out.append({"id": f"{rel[:-3].replace(os.sep, '.')}.{m.group(1)}", "ref": f"{rel}:{m.group(1)}", "via": "scan"})
    return out


def runner_cmd(job_dir: str, mode: str, repo: str, ref: str):
    return [os.path.join(job_dir, "venv", "bin", "python"), RUNNER, mode, repo, ref]


def parse_lines(out: str) -> List[dict]:
    res = []
    for l in out.splitlines():
        l = l.strip()
        if l.startswith("{"):
            try: res.append(json.loads(l))
            except Exception: pass
    return res


def inspect_ref(job_dir, repo, ref) -> dict:
    p = subprocess.run(runner_cmd(job_dir, "inspect", repo, ref), cwd=repo, env=sub_env(), capture_output=True, text=True, timeout=INSPECT_TIMEOUT)
    evs = parse_lines(p.stdout)
    for e in evs:
        if e.get("type") == "graph": return e
    err = next((e for e in evs if e.get("type") == "error"), None)
    raise ImportError_((err or {}).get("errors", [p.stderr.strip()[-800:] or "Could not inspect the graph"])[0])


def required_env(repo: str) -> List[str]:
    keys = []
    for f in (".env.example", ".env.sample", ".env.template"):
        p = os.path.join(repo, f)
        if os.path.exists(p):
            for l in open(p, errors="ignore"):
                m = re.match(r"^\s*([A-Z][A-Z0-9_]*(?:KEY|TOKEN))\s*=", l)
                if m: keys.append(m.group(1))
    return keys


def do_import(job_id: str):
    job = JOBS[job_id]; d = job["dir"]
    try:
        job["status"] = "fetching"
        src = os.path.join(d, "src_raw")
        if job["kind"] == "url":
            cmd = ["git", "clone", "--depth", "1"] + (["--branch", job["branch"]] if job.get("branch") else []) + [job["url"], src]
            _sh(job, cmd, timeout=180)
        else:
            os.makedirs(src); src = safe_extract(job["zip_path"], src)
        repo = os.path.realpath(os.path.join(src, job.get("subdir") or ""))
        if not repo.startswith(os.path.realpath(d)) or not os.path.isdir(repo): raise ImportError_("Invalid subdir")
        job["repo"] = repo
        job["status"] = "installing"
        _sh(job, ["uv", "venv", "-q", os.path.join(d, "venv"), "--python", sys.executable] if shutil.which("uv") else [sys.executable, "-m", "venv", os.path.join(d, "venv")])
        py = os.path.join(d, "venv", "bin", "python")
        pip = ["uv", "pip", "install", "-q", "--python", py] if shutil.which("uv") else [py, "-m", "pip", "install", "-q"]
        if os.path.exists(os.path.join(repo, "pyproject.toml")) or os.path.exists(os.path.join(repo, "setup.py")):
            _sh(job, pip + ["-e", repo, "langgraph", "python-dotenv"])
        elif os.path.exists(os.path.join(repo, "requirements.txt")):
            _sh(job, pip + ["-r", os.path.join(repo, "requirements.txt"), "langgraph", "python-dotenv"])
        else:
            _sh(job, pip + ["langgraph", "python-dotenv"])
        job["status"] = "inspecting"
        refs = find_graphs(repo)
        if not refs: raise ImportError_("No graph found (langgraph.json or a compiled StateGraph variable)")
        _log(job, f"Found {len(refs)} graph(s): " + ", ".join(r["ref"] for r in refs))
        graphs = []
        for r in refs:
            try:
                g = inspect_ref(d, repo, r["ref"]); graphs.append({**r, "graph": g}); _log(job, f"✓ {r['id']}: {len(g['nodes'])} nodes, {len(g['edges'])} edges")
            except Exception as e:
                _log(job, f"✗ {r['id']}: {e}")
        if not graphs: raise ImportError_("No graph could be loaded (see log)")
        job["graphs"] = graphs; job["required_env"] = required_env(repo)
        job["status"] = "ready"; _log(job, "Done — pick a graph to create a workflow")
    except subprocess.TimeoutExpired as e:
        job["status"] = "error"; job["error"] = f"Timeout: {e.cmd[0]}"; _log(job, job["error"])
    except Exception as e:
        job["status"] = "error"; job["error"] = str(e); _log(job, f"Error: {e}")


def start_job(owner: str, kind: str, url: str = None, branch: str = None, subdir: str = None, zip_bytes: bytes = None, sync=False) -> str:
    if kind == "url" and not GH_RE.match(url or ""): raise ImportError_("Only public GitHub URLs like https://github.com/owner/repo are supported")
    if branch and not re.match(r"^[\w./-]+$", branch): raise ImportError_("Invalid branch")
    if subdir and (".." in subdir.split("/") or subdir.startswith("/")): raise ImportError_("Invalid subdir")
    jid = uuid.uuid4().hex[:10]; d = os.path.realpath(os.path.join(ROOT, jid)); os.makedirs(d)
    job = {"id": jid, "owner": owner, "kind": kind, "url": url, "branch": branch, "subdir": subdir, "dir": d,
           "status": "queued", "log": [], "graphs": [], "error": None, "created": time.time()}
    if zip_bytes is not None:
        job["zip_path"] = os.path.join(d, "upload.zip"); open(job["zip_path"], "wb").write(zip_bytes)
    JOBS[jid] = job
    if sync: do_import(jid)
    else: threading.Thread(target=do_import, args=(jid,), daemon=True).start()
    return jid


def public_job(job):
    return {k: job[k] for k in ("id", "status", "log", "error", "url", "branch", "subdir")} | {
        "graphs": [{"id": g["id"], "ref": g["ref"], "via": g["via"], "name": g["graph"].get("name"), "nodes": len(g["graph"]["nodes"]), "edges": len(g["graph"]["edges"])} for g in job["graphs"]],
        "required_env": job.get("required_env", [])}


def to_workflow(job: dict, gid: str) -> dict:
    g = next(x for x in job["graphs"] if x["id"] == gid); gr = g["graph"]
    nodes = []
    for n in gr["nodes"]:
        t = "start" if n["id"] == "__start__" else "end" if n["id"] == "__end__" else "code"
        data = {"label": "Start" if t == "start" else "End" if t == "end" else n["id"]}
        if t == "code":
            data.update({"node_name": n["id"], "ref": n.get("ref"), "source": n.get("source"), "is_llm": n.get("is_llm", False), "kind": n.get("kind"), "subgraph": n.get("subgraph", False)})
        nodes.append({"id": n["id"], "type": t, "position": {"x": 0, "y": 0}, "data": data})
    edges = []
    for i, e in enumerate(gr["edges"]):
        ed = {"id": f"e{i}", "source": e["source"], "target": e["target"], "conditional": e["conditional"]}
        if e["conditional"]: ed["label"] = e.get("label") or e["target"]
        edges.append(ed)
    name = gr.get("name") if gr.get("name") not in (None, "LangGraph") else gid
    repo_name = (job.get("url") or "upload.zip").rstrip("/").split("/")[-1].removesuffix(".git")
    return {"name": f"{repo_name}: {name}", "state": gr.get("state", []), "nodes": nodes, "edges": edges, "needs_layout": True,
            "source": {"kind": "langgraph_import", "import_id": job["id"], "graph_id": gid, "ref": g["ref"], "repo_url": job.get("url"),
                       "branch": job.get("branch"), "subdir": job.get("subdir"), "repo_dir": job["repo"], "job_dir": job["dir"],
                       "required_env": job.get("required_env", []), "imported_at": time.time()}}


def run_imported(wf: dict, inp: dict, on_proc=None, resume: dict | None = None, checkpointing: bool = False):
    """Sync generator: run original compiled graph in its venv subprocess and yield events.
    checkpointing: the runner attaches an in-memory LangGraph saver (when the graph has none) and yields `_checkpoint`
    {node, nodes, blob} after each superstep; resume = {"blob"} continues such a checkpoint (TASK-0021)."""
    s = wf["source"]
    inp = {**inp, **({"__checkpointing__": True} if checkpointing else {}), **({"__resume__": resume["blob"]} if resume and resume.get("blob") else {})}
    missing = [k for k in s.get("required_env", []) if k not in os.environ and not _in_dotenv(s["repo_dir"], k)]
    if not os.path.exists(os.path.join(s["job_dir"], "venv", "bin", "python")):
        yield {"type": "error", "errors": ["The import environment is gone (venv deleted). Please import the repo again."]}; return
    p = subprocess.Popen(runner_cmd(s["job_dir"], "run", s["repo_dir"], s["ref"]), cwd=s["repo_dir"], env=sub_env(),
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    timer = threading.Timer(RUN_TIMEOUT, p.kill); timer.start()
    p.stdin.write(json.dumps(inp)); p.stdin.close()
    got_end = False
    try:
        for line in p.stdout:
            line = line.strip()
            if not line.startswith("{"): continue
            try: ev = json.loads(line)
            except Exception: continue
            if ev.get("type") == "error" and missing:
                ev["errors"] = ev.get("errors", []) + [f"The repo requires variables: {', '.join(missing)} (not set in the server env or the repo .env)"]
            ev.pop("trace", None)
            if ev.get("node"): ev.setdefault("label", {"__start__": "Start", "__end__": "End"}.get(ev["node"], ev["node"]))
            if ev.get("type") in ("run_finished", "error"): got_end = True
            yield ev
        p.wait()
    finally:
        timer.cancel()
        if p.poll() is None: p.kill()  # generator closed early (cancel/timeout) -> stop the subprocess
    if not got_end:
        err = p.stderr.read()[-800:]
        yield {"type": "error", "errors": [f"Subprocess exited abnormally (code {p.returncode}, possibly a {RUN_TIMEOUT}s timeout). {err}"]}


def _in_dotenv(repo, key):
    p = os.path.join(repo, ".env")
    return os.path.exists(p) and any(l.strip().startswith(key + "=") and l.strip() != key + "=" for l in open(p, errors="ignore"))
