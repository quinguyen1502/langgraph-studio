"""Smoke test for STUDIO_CODE_RUNTIME=remote (CI: .github/workflows/image.yml): the studio reports the remote runtime,
runs Python and TypeScript in the sandbox service, and the sandbox refuses sockets and processes and has none of the
studio's secrets. Usage: SMOKE_EMAIL=... SMOKE_PASSWORD=... python scripts/sandbox_smoke.py http://localhost:8090"""
import os, sys
import httpx

BASE = sys.argv[1].rstrip("/")
c = httpx.Client(base_url=BASE, timeout=60)
tok = c.post("/api/auth/login", json={"email": os.environ["SMOKE_EMAIL"], "password": os.environ["SMOKE_PASSWORD"]}).json()["data"]["token"]
H = {"Authorization": f"Bearer {tok}"}


def test(source, language="python", state=None):
    r = c.post("/api/code/test", headers=H, json={"source": source, "language": language, "state": state or {}}).json()
    assert r["success"], r
    return r["data"]


rt = c.get("/api/meta/runtime", headers=H).json()["data"]
print("runtime:", rt["code_runtime"], {x["id"]: x["available"] for x in rt["languages"]})
assert rt["code_runtime"] == "remote" and rt["available"] and all(x["available"] for x in rt["languages"]), rt

d = test('def main(state):\n    print("hi")\n    return state["n"] * 2\n', state={"n": 21})
assert d["ok"] and d["value"] == 42 and d["runtime"] == "remote" and d["stdout"] == "hi\n", d

d = test('import os, pydantic\ndef main(state):\n    return {"uid": os.getuid(), "env": sorted(os.environ)}\n')
assert d["ok"] and d["value"]["uid"] >= 61000, d                      # its own uid, not root
assert not any(k.startswith(("JWT", "DATABASE", "STUDIO_SECRET", "STUDIO_SANDBOX")) for k in d["value"]["env"]), d

d = test('import socket\ndef main(state):\n    socket.create_connection(("1.1.1.1", 443), timeout=3)\n')
assert not d["ok"] and "PermissionError" in d["error"]["message"], d
d = test('import subprocess\ndef main(state):\n    return subprocess.run(["id"]).returncode\n')
assert not d["ok"] and "PermissionError" in d["error"]["message"], d

d = test('import { z } from "npm:zod@3"\nexport function main(state: { s: string }) { return z.string().parse(state.s).length }\n',
         "typescript", {"s": "four"})
assert d["ok"] and d["value"] == 4 and d["runtime"] == "remote", d
d = test('export async function main() { return (await fetch("https://example.com")).status }\n', "typescript")
assert not d["ok"], d                                                   # Deno has no net permission
print("SANDBOX SMOKE OK")
