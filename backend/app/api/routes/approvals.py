"""Approval through external channels (TASK-0022, DEC-0019).

User (JWT): channel connections (personal; org-wide ones need an admin), own channel identities (link, one-time code, verify), audit log.
Platforms (no JWT; verified by signature / secret header): POST /api/approvals/callback/{kind}/{channel_id}, or the
shared POST /api/approvals/callback/slack routed by team_id.
"""
import asyncio
from typing import Optional
from fastapi import APIRouter, Body, Depends, Request
from ...core import config
from ..deps import approval_service, channel_service, current_user, identity_service

router = APIRouter(prefix="/api/approvals", tags=["approvals"])


@router.get("/channels")
def list_channels(user=Depends(current_user), svc=Depends(channel_service)): return svc.list(user["id"])

@router.post("/channels")
def create_channel(body=Body(None), user=Depends(current_user), svc=Depends(channel_service)): return svc.create(user["id"], body)

@router.put("/channels/{cid}")
def update_channel(cid: str, body=Body(None), user=Depends(current_user), svc=Depends(channel_service)): return svc.update(user["id"], cid, body)

@router.delete("/channels/{cid}")
def delete_channel(cid: str, user=Depends(current_user), svc=Depends(channel_service)): return svc.delete(user["id"], cid)

@router.post("/channels/{cid}/register-webhook")
def register_webhook(cid: str, user=Depends(current_user), svc=Depends(channel_service)): return svc.register_webhook(user["id"], cid)

@router.get("/identities")
def get_identities(user=Depends(current_user), svc=Depends(identity_service)): return svc.get(user["id"])

@router.put("/identities")
def put_identities(body=Body(None), user=Depends(current_user), svc=Depends(identity_service)): return svc.link(user["id"], body)

@router.post("/identities/{kind}/send-code")
def send_code(kind: str, user=Depends(current_user), svc=Depends(identity_service)): return svc.send_code(user["id"], kind)

@router.post("/identities/{kind}/verify")
def verify_identity(kind: str, body=Body(None), user=Depends(current_user), svc=Depends(identity_service)): return svc.verify(user["id"], kind, body)

@router.get("/audit")
def audit(user=Depends(current_user), svc=Depends(approval_service)): return svc.audit_log(user["id"])


def client_ip(request: Request) -> str:
    """The caller's IP. Behind our reverse proxy (STUDIO_TRUST_PROXY=1) the last X-Forwarded-For hop, which the
    proxy appended itself; earlier hops are client-controlled and ignored."""
    fwd = request.headers.get("x-forwarded-for") if config.trust_proxy() else None
    if fwd and fwd.split(",")[-1].strip(): return fwd.split(",")[-1].strip()
    return request.client.host if request.client else "unknown"


async def _callback(kind: str, cid: Optional[str], request: Request, svc):
    body = await request.body()
    await svc.check_rate(client_ip(request), kind, cid, body)  # 429 RATE_LIMITED
    return await asyncio.to_thread(svc.handle_callback, kind, cid, dict(request.headers), body)


@router.post("/callback/{kind}")
async def shared_callback(kind: str, request: Request, svc=Depends(approval_service)):
    """One URL for every connection of the kind (Slack: routed by the payload's team.id, then the signature)."""
    return await _callback(kind, None, request, svc)


@router.post("/callback/{kind}/{cid}")
async def callback(kind: str, cid: str, request: Request, svc=Depends(approval_service)):
    """Slack interactivity / Telegram webhook. Refusals (expired, not allowed, ...) are answered in the channel and
    return 200 so the platform does not retry; only an unauthenticated request gets 401."""
    return await _callback(kind, cid, request, svc)
