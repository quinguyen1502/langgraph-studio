"""WebSocket run controller: auth + socket I/O only; the run lifecycle lives in RunService."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ...core.errors import DomainError, Unauthorized
from ...services.auth_service import AuthService
from ..deps import run_service

router = APIRouter()


@router.websocket("/ws/run")
async def ws_run(ws: WebSocket):
    """Connect with ?token=JWT. Client sends {workflow_id, workflow?, input}; server streams events.
    While running, the client may send {"type": "cancel"}; closing the socket also cancels.
    Final status: ok | error | cancelled | timeout (stored in run history)."""
    try:
        uid = AuthService.user_from_token(ws.query_params.get("token") or "")["id"]
    except Unauthorized:
        await ws.close(code=4401); return
    await ws.accept()
    try:
        req = await ws.receive_json()
    except (WebSocketDisconnect, ValueError, KeyError):
        return
    svc = run_service()
    try:
        plan = svc.plan(uid, req)
    except DomainError as e:
        await ws.send_json({"type": "error", "errors": [e.message]}); await ws.close(); return

    state = {"connected": True}

    async def send(ev) -> bool:
        try: await ws.send_json(ev); return True
        except Exception: state["connected"] = False; return False

    async def listen() -> str:
        try:
            while True:
                m = await ws.receive_json()
                if isinstance(m, dict) and m.get("type") == "cancel": return "cancelled"
        except (WebSocketDisconnect, RuntimeError, ValueError):
            state["connected"] = False
            return "disconnected"

    await svc.execute(plan, send, listen)
    if state["connected"]:
        try: await ws.close()
        except Exception: pass
