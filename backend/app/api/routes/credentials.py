from fastapi import APIRouter, Depends
from ...schemas.credential import CredentialIn
from ..deps import credential_service, current_user

router = APIRouter(prefix="/api", tags=["credentials"])

@router.get("/providers")
def providers(user=Depends(current_user), svc=Depends(credential_service)): return svc.providers()

@router.get("/credentials")
def list_creds(user=Depends(current_user), svc=Depends(credential_service)): return svc.list(user["id"])

@router.post("/credentials")
def create_cred(body: CredentialIn, user=Depends(current_user), svc=Depends(credential_service)):
    return svc.create(user["id"], body.name, body.provider, body.api_key, body.base_url)

@router.delete("/credentials/{cid}")
def delete_cred(cid: str, user=Depends(current_user), svc=Depends(credential_service)): return svc.delete(cid, user["id"])
