"""Approval through external channels (TASK-0022, DEC-0019).

Owner (JWT): channel connections, own channel identities, audit log.
Platforms (no JWT; verified by signature / secret header): POST /api/approvals/callback/{kind}/{channel_id}.
"""
import asyncio
from fastapi import APIRouter, Body, Depends, Request
from ..deps import approval_service, current_user

router = APIRouter(prefix="/api/approvals", tags=["approvals"])


@router.get("/channels")
def list_channels(user=Depends(current_user), svc=Depends(approval_service)): return svc.list_channels(user["id"])

@router.put("/channels/{kind}")
def save_channel(kind: str, body=Body(None), user=Depends(current_user), svc=Depends(approval_service)): return svc.save_channel(user["id"], kind, body)

@router.delete("/channels/{kind}")
def delete_channel(kind: str, user=Depends(current_user), svc=Depends(approval_service)): return svc.delete_channel(user["id"], kind)

@router.post("/channels/{kind}/register-webhook")
def register_webhook(kind: str, user=Depends(current_user), svc=Depends(approval_service)): return svc.register_webhook(user["id"], kind)

@router.get("/identities")
def get_identities(user=Depends(current_user), svc=Depends(approval_service)): return svc.identities(user["id"])

@router.put("/identities")
def put_identities(body=Body(None), user=Depends(current_user), svc=Depends(approval_service)): return svc.set_identities(user["id"], body)

@router.get("/audit")
def audit(user=Depends(current_user), svc=Depends(approval_service)): return svc.audit_log(user["id"])


@router.post("/callback/{kind}/{cid}")
async def callback(kind: str, cid: str, request: Request, svc=Depends(approval_service)):
    """Slack interactivity / Telegram webhook. Refusals (expired, not allowed, ...) are answered in the channel and
    return 200 so the platform does not retry; only an unauthenticated request gets 401."""
    body = await request.body()
    return await asyncio.to_thread(svc.handle_callback, kind, cid, dict(request.headers), body)
