from typing import Optional
from fastapi import APIRouter, Depends, File, UploadFile
from ...core.errors import AppError
from ...schemas.knowledge import KnowledgeBaseIn, SearchIn
from ...services.knowledge_service import MAX_BYTES
from ...core import permissions as P
from ..deps import current_user, knowledge_service, need

router = APIRouter(prefix="/api/knowledge-bases", tags=["knowledge"])

@router.get("")
def list_kbs(user=Depends(current_user), svc=Depends(knowledge_service)): return svc.list(user["id"])

@router.post("")
def create_kb(body: KnowledgeBaseIn, user=Depends(need(P.RESOURCES_MANAGE)), svc=Depends(knowledge_service)):
    return svc.create(user["id"], body.name, body.description, body.model, body.credential_id)

@router.get("/{kid}")
def get_kb(kid: str, user=Depends(current_user), svc=Depends(knowledge_service)): return svc.get(kid, user["id"])

@router.put("/{kid}")
def update_kb(kid: str, body: KnowledgeBaseIn, user=Depends(need(P.RESOURCES_MANAGE)), svc=Depends(knowledge_service)):
    return svc.update(kid, user["id"], body.name, body.description, body.model, body.credential_id)

@router.delete("/{kid}")
def delete_kb(kid: str, user=Depends(need(P.RESOURCES_MANAGE)), svc=Depends(knowledge_service)): return svc.delete(kid, user["id"])

@router.post("/{kid}/documents")
async def upload(kid: str, file: Optional[UploadFile] = File(None), user=Depends(need(P.RESOURCES_MANAGE)), svc=Depends(knowledge_service)):
    if file is None: raise AppError("KB_FILE_REQUIRED")
    data = await file.read(MAX_BYTES + 1)  # one byte over the limit is enough to reject
    return svc.upload(kid, user["id"], file.filename or "", data)

@router.delete("/{kid}/documents/{did}")
def delete_document(kid: str, did: str, user=Depends(need(P.RESOURCES_MANAGE)), svc=Depends(knowledge_service)):
    return svc.delete_document(kid, did, user["id"])

@router.post("/{kid}/reindex")
def reindex(kid: str, user=Depends(need(P.RESOURCES_MANAGE)), svc=Depends(knowledge_service)): return svc.reindex(kid, user["id"])

@router.post("/{kid}/search")
def search(kid: str, body: SearchIn, user=Depends(current_user), svc=Depends(knowledge_service)):
    return svc.search(kid, user["id"], body.query, body.top_k)
