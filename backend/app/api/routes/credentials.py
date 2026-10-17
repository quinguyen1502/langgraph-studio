from fastapi import APIRouter, Depends
from ...schemas.credential import CredentialIn, CredentialUpdate, EmbeddingTestIn, ProviderProbeIn
from ...core import permissions as P
from ..deps import credential_service, current_user, need

router = APIRouter(prefix="/api", tags=["credentials"])

@router.get("/providers")
def providers(user=Depends(current_user), svc=Depends(credential_service)): return svc.providers()

@router.post("/providers/{pid}/test")
def probe_provider(pid: str, body: ProviderProbeIn, user=Depends(need(P.RESOURCES_MANAGE)), svc=Depends(credential_service)):
    return svc.probe(pid, body.api_key, body.base_url, body.headers, user["id"], body.credential_id)

@router.get("/credentials")
def list_creds(user=Depends(current_user), svc=Depends(credential_service)): return svc.list(user["id"])

@router.post("/credentials")
def create_cred(body: CredentialIn, user=Depends(need(P.RESOURCES_MANAGE)), svc=Depends(credential_service)):
    return svc.create(user["id"], body.name, body.provider, body.api_key, body.base_url, body.headers)

@router.get("/credentials/{cid}/models")
def credential_models(cid: str, user=Depends(current_user), svc=Depends(credential_service)): return svc.models(user["id"], cid)

@router.put("/credentials/{cid}")
def update_cred(cid: str, body: CredentialUpdate, user=Depends(need(P.RESOURCES_MANAGE)), svc=Depends(credential_service)):
    return svc.update(user["id"], cid, body.name, body.base_url, body.headers, body.api_key, body.clear_key)

@router.post("/credentials/{cid}/embeddings/test")
def embedding_test(cid: str, body: EmbeddingTestIn, user=Depends(current_user), svc=Depends(credential_service)):
    return svc.embedding_test(user["id"], cid, body.model)

@router.delete("/credentials/{cid}")
def delete_cred(cid: str, user=Depends(need(P.RESOURCES_MANAGE)), svc=Depends(credential_service)): return svc.delete(cid, user["id"])
