"""API / webhook triggers (TASK-0007).

Owner (JWT): manage per-workflow tokens under /api/workflows/{wid}/tokens.
External callers (workflow token, `Authorization: Bearer wft_…` or `X-Workflow-Token`):
  POST /api/hooks/workflows/{wid}/runs  {input, mode: async|sync, callback_url?}
  GET  /api/hooks/workflows/{wid}/runs/{run_id}
"""
from typing import Optional
from fastapi import APIRouter, Depends, Header
from ...core import config
from ...schemas.envelope import EnvelopeResponse
from ...schemas.trigger import TokenIn, TriggerIn
from ..deps import current_user, trigger_service

router = APIRouter(prefix="/api", tags=["triggers"])


def workflow_token(authorization: Optional[str] = Header(None), x_workflow_token: Optional[str] = Header(None)) -> Optional[str]:
    if x_workflow_token: return x_workflow_token.strip()
    if authorization and authorization.lower().startswith("bearer "): return authorization[7:].strip()
    return None


@router.get("/workflows/{wid}/tokens")
def list_tokens(wid: str, user=Depends(current_user), svc=Depends(trigger_service)): return svc.list_tokens(wid, user["id"])

@router.post("/workflows/{wid}/tokens")
def create_token(wid: str, body: TokenIn, user=Depends(current_user), svc=Depends(trigger_service)): return svc.create_token(wid, user["id"], body.name)

@router.delete("/workflows/{wid}/tokens/{tid}")
def revoke_token(wid: str, tid: str, user=Depends(current_user), svc=Depends(trigger_service)): return svc.revoke_token(wid, tid, user["id"])


@router.post("/hooks/workflows/{wid}/runs")
async def trigger_run(wid: str, body: TriggerIn, token: Optional[str] = Depends(workflow_token), svc=Depends(trigger_service)):
    tok = svc.authenticate(wid, token)
    rid = svc.start(tok, body.input, body.callback_url)
    if body.mode == "async":
        return EnvelopeResponse({"run_id": rid, "status": "queued"}, status_code=202)
    res = await svc.wait(tok, rid, config.run_timeout() + 5)
    return res if res["status"] not in ("queued", "running") else EnvelopeResponse(res, status_code=202)  # still running: poll the GET endpoint

@router.get("/hooks/workflows/{wid}/runs/{run_id}")
def run_status(wid: str, run_id: str, token: Optional[str] = Depends(workflow_token), svc=Depends(trigger_service)):
    return svc.result(svc.authenticate(wid, token), run_id)
