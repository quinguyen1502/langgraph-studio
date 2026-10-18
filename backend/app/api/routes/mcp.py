from fastapi import APIRouter, Depends
from ...schemas.mcp import McpServerIn
from ...core import permissions as P
from ..deps import current_user, mcp_service, need

router = APIRouter(prefix="/api/mcp/servers", tags=["mcp"])

@router.get("")
def list_servers(user=Depends(current_user), svc=Depends(mcp_service)): return svc.list(user["id"])

@router.post("")
def create_server(body: McpServerIn, user=Depends(need(P.RESOURCES_MANAGE)), svc=Depends(mcp_service)):
    return svc.create(user["id"], body.name, body.transport, body.scope, body.command, body.args, body.url, body.secrets)

@router.put("/{sid}")
def update_server(sid: str, body: McpServerIn, user=Depends(need(P.RESOURCES_MANAGE)), svc=Depends(mcp_service)):
    return svc.update(sid, user["id"], body.name, body.command, body.args, body.url, body.secrets)

@router.delete("/{sid}")
def delete_server(sid: str, user=Depends(need(P.RESOURCES_MANAGE)), svc=Depends(mcp_service)): return svc.delete(sid, user["id"])

@router.post("/{sid}/discover")
def discover(sid: str, user=Depends(need(P.RESOURCES_MANAGE)), svc=Depends(mcp_service)): return svc.discover(sid, user["id"])
