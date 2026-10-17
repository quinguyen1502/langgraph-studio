"""User administration and workflow sharing (TASK-0014)."""
from fastapi import APIRouter, Depends
from ...core import permissions as P
from ...schemas.rbac import ShareIn, UserUpdate
from ..deps import current_user, share_service, user_service

router = APIRouter(prefix="/api", tags=["rbac"])

@router.get("/roles")
def roles(user=Depends(current_user)): return P.matrix()

@router.get("/admin/users")
def list_users(user=Depends(current_user), svc=Depends(user_service)): return svc.list(user["id"])

@router.patch("/admin/users/{target}")
def update_user(target: str, body: UserUpdate, user=Depends(current_user), svc=Depends(user_service)):
    return svc.update(user["id"], target, body.role, body.active)

@router.get("/workflows/{wid}/shares")
def list_shares(wid: str, user=Depends(current_user), svc=Depends(share_service)): return svc.list(wid, user["id"])

@router.put("/workflows/{wid}/shares")
def put_share(wid: str, body: ShareIn, user=Depends(current_user), svc=Depends(share_service)): return svc.put(wid, user["id"], body.email, body.role)

@router.delete("/workflows/{wid}/shares/{target}")
def delete_share(wid: str, target: str, user=Depends(current_user), svc=Depends(share_service)): return svc.remove(wid, user["id"], target)
