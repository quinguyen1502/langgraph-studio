"""Smoke test for a running stack (docker compose or dev): health, demo login, seeded example run over /ws/run.
Usage: python scripts/compose_smoke.py [http://localhost:8080]   (needs `httpx` and `websockets`)"""
import asyncio, json, sys
import httpx, websockets

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080").rstrip("/")


async def main():
    with httpx.Client(base_url=BASE, timeout=10) as c:
        health = c.get("/api/health").json()["data"]; print("health:", health)
        tok = c.post("/api/auth/login", json={"email": "admin@example.com", "password": "admin123"}).json()["data"]["token"]
        H = {"Authorization": f"Bearer {tok}"}
        wf = c.get("/api/workflows", headers=H).json()["data"][0]; print("workflow:", wf["name"])
        assert c.post("/api/runs/nope/cancel", headers=H).json()["error"]["code"] == "RUN_NOT_FOUND"
    ws_url = BASE.replace("http", "ws", 1) + f"/ws/run?token={tok}"
    async with websockets.connect(ws_url) as ws:
        await ws.send(json.dumps({"workflow_id": wf["id"], "input": {"question": "hello"}}))
        types = []
        async for raw in ws:
            ev = json.loads(raw); types.append(ev["type"])
            if ev["type"] in ("run_finished", "error", "run_cancelled"): break
    print("events:", " ".join(types))
    assert types[0] == "run_started" and types[-1] == "run_finished", types
    with httpx.Client(base_url=BASE, timeout=10) as c:
        runs = c.get(f"/api/workflows/{wf['id']}/runs", headers=H).json()["data"]
        print("history:", len(runs), "latest status:", runs[0]["status"])
    print("SMOKE OK")


asyncio.run(main())


def api_trigger_check():
    """TASK-0007: token + sync trigger through nginx (executed by the worker service via the Redis queue)."""
    with httpx.Client(base_url=BASE, timeout=60) as c:
        tok = c.post("/api/auth/login", json={"email": "admin@example.com", "password": "admin123"}).json()["data"]["token"]
        wid = c.get("/api/workflows", headers={"Authorization": f"Bearer {tok}"}).json()["data"][0]["id"]
        secret = c.post(f"/api/workflows/{wid}/tokens", json={"name": "smoke"}, headers={"Authorization": f"Bearer {tok}"}).json()["data"]["token"]
        d = c.post(f"/api/hooks/workflows/{wid}/runs", json={"input": {"message": "refund"}, "mode": "sync"},
                   headers={"Authorization": f"Bearer {secret}"}).json()["data"]
        print("api trigger:", d["status"], d["source"], d["final_state"]["intent"])
        assert d["status"] == "ok" and d["source"] == "api"
    print("API TRIGGER OK")


api_trigger_check()
