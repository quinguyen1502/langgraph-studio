from typing import Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile
from ...schemas.imports import Finalize
from ...core import permissions as P
from ..deps import current_user, import_service, need

router = APIRouter(prefix="/api", tags=["import"])

@router.post("/import")
async def import_repo(url: Optional[str] = Form(None), branch: Optional[str] = Form(None), subdir: Optional[str] = Form(None),
                      file: Optional[UploadFile] = File(None), user=Depends(need(P.WORKFLOWS_CREATE)), svc=Depends(import_service)):
    data = await file.read() if file is not None else None
    return svc.start(user["id"], url=url, branch=branch, subdir=subdir, zip_bytes=data)

@router.get("/import/{jid}")
def import_status(jid: str, user=Depends(current_user), svc=Depends(import_service)): return svc.status(jid, user["id"])

@router.post("/import/{jid}/finalize")
def import_finalize(jid: str, body: Finalize, user=Depends(need(P.WORKFLOWS_CREATE)), svc=Depends(import_service)):
    return svc.finalize(jid, body.graph_id, user["id"])
