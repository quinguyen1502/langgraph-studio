from fastapi import APIRouter, Depends
from ...schemas.auth import Credentials
from ..deps import auth_service, current_user

router = APIRouter(prefix="/api", tags=["auth"])

@router.post("/auth/register")
def register(cr: Credentials, svc=Depends(auth_service)): return svc.register(cr.email, cr.password)

@router.post("/auth/login")
def login(cr: Credentials, svc=Depends(auth_service)): return svc.login(cr.email, cr.password)

@router.get("/me")
def me(user=Depends(current_user)): return user
