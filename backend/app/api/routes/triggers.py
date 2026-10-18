"""API / webhook triggers (TASK-0007).

Owner (JWT): manage per-workflow tokens under /api/workflows/{wid}/tokens and cron schedules (TASK-0046) under
/api/workflows/{wid}/schedules; POST /api/schedules/preview lists the next times of an expression.
External callers (workflow token, `Authorization: Bearer wft_…` or `X-Workflow-Token`):
  POST /api/hooks/workflows/{wid}/runs  {input, mode: async|sync, callback_url?}
  GET  /api/hooks/workflows/{wid}/runs/{run_id}
"""
from typing import Optional
import asyncio
from fastapi import APIRouter, Depends, Header, Request
from ...core import config
from ...schemas.envelope import EnvelopeResponse
from ...schemas.trigger import ScheduleIn, SchedulePatch, SchedulePreview, TokenIn, TriggerIn
from ..deps import current_user, delivery_service, schedule_service, trigger_service

router = APIRouter(prefix="/api", tags=["triggers"])


def workflow_token(authorization: Optional[str] = Header(None), x_workflow_token: Optional[str] = Header(None)) -> Optional[str]:
    if x_workflow_token: return x_workflow_token.strip()
    if authorization and authorization.lower().startswith("bearer "): return authorization[7:].strip()
    return None


@router.get("/workflows/{wid}/tokens")
def list_tokens(wid: str, user=Depends(current_user), svc=Depends(trigger_service)): return svc.list_tokens(wid, user["id"])

@router.post("/workflows/{wid}/tokens")
def create_token(wid: str, body: TokenIn, user=Depends(current_user), svc=Depends(trigger_service)): return svc.create_token(wid, user["id"], body.name)

@router.post("/workflows/{wid}/tokens/{tid}/rotate-secret")
def rotate_secret(wid: str, tid: str, user=Depends(current_user), svc=Depends(trigger_service)): return svc.rotate_secret(wid, tid, user["id"])

@router.get("/workflows/{wid}/deliveries")
def list_deliveries(wid: str, user=Depends(current_user), svc=Depends(delivery_service)): return svc.list(wid, user["id"])

@router.post("/workflows/{wid}/deliveries/{did}/redeliver")
def redeliver(wid: str, did: str, user=Depends(current_user), svc=Depends(delivery_service)): return svc.redeliver(wid, did, user["id"])

@router.delete("/workflows/{wid}/tokens/{tid}")
def revoke_token(wid: str, tid: str, user=Depends(current_user), svc=Depends(trigger_service)): return svc.revoke_token(wid, tid, user["id"])


@router.post("/hooks/workflows/{wid}/runs")
async def trigger_run(wid: str, body: TriggerIn, request: Request, token: Optional[str] = Depends(workflow_token), svc=Depends(trigger_service)):
    tok = await asyncio.to_thread(svc.authenticate, wid, token)
    await svc.check_rate(tok)  # 429 RATE_LIMITED + Retry-After
    rid = await asyncio.to_thread(svc.start, tok, body.input, body.callback_url)
    poll = poll_url(request, wid, rid)
    if body.mode == "async":
        return EnvelopeResponse({"run_id": rid, "status": "queued", "poll_url": poll}, status_code=202)
    res = await svc.wait(tok, rid, min(config.sync_wait_max(), config.run_timeout() + 5))
    if res["status"] in ("queued", "running"):  # still going after STUDIO_SYNC_WAIT_MAX: poll instead of holding the connection
        return EnvelopeResponse({**res, "poll_url": poll}, status_code=202, headers={"Location": poll})
    return res


def poll_url(request: Request, wid: str, rid: str) -> str:
    return str(request.url_for("run_status", wid=wid, run_id=rid))

@router.get("/hooks/workflows/{wid}/runs/{run_id}")
def run_status(wid: str, run_id: str, token: Optional[str] = Depends(workflow_token), svc=Depends(trigger_service)):
    return svc.result(svc.authenticate(wid, token), run_id)


# ---- cron schedules (TASK-0046) ----
@router.get("/workflows/{wid}/schedules")
def list_schedules(wid: str, user=Depends(current_user), svc=Depends(schedule_service)): return svc.list(wid, user["id"])

@router.post("/workflows/{wid}/schedules")
def create_schedule(wid: str, body: ScheduleIn, user=Depends(current_user), svc=Depends(schedule_service)):
    return svc.create(wid, user["id"], body.name, body.cron, body.timezone, body.input, body.enabled)

@router.patch("/workflows/{wid}/schedules/{sid}")
def update_schedule(wid: str, sid: str, body: SchedulePatch, user=Depends(current_user), svc=Depends(schedule_service)):
    return svc.update(wid, sid, user["id"], **body.model_dump())

@router.delete("/workflows/{wid}/schedules/{sid}")
def delete_schedule(wid: str, sid: str, user=Depends(current_user), svc=Depends(schedule_service)): return svc.delete(wid, sid, user["id"])

@router.post("/schedules/preview")
def preview_schedule(body: SchedulePreview, user=Depends(current_user), svc=Depends(schedule_service)): return svc.preview(body.cron, body.timezone)
