import time
from fastapi import APIRouter, Depends, Response
from ...core import config, permissions as P, security
from ...schemas.auth import Credentials, ResetConfirm, ResetRequest
from ..deps import auth_service, current_user, need

router = APIRouter(prefix="/api", tags=["auth"])


def _signed_in(session: dict, response: Response) -> dict:
    """The browser keeps the JWT in an HttpOnly cookie (TASK-0045). The body still has `token` for API clients."""
    response.set_cookie(security.SESSION_COOKIE, session["token"], max_age=max(1, session["expires_at"] - int(time.time())),
                        httponly=True, samesite="lax", secure=config.cookie_secure(), path="/")
    return session


@router.post("/auth/register")
def register(cr: Credentials, response: Response, svc=Depends(auth_service)): return _signed_in(svc.register(cr.email, cr.password), response)

@router.post("/auth/login")
def login(cr: Credentials, response: Response, svc=Depends(auth_service)): return _signed_in(svc.login(cr.email, cr.password), response)

@router.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie(security.SESSION_COOKIE, path="/", httponly=True, samesite="lax", secure=config.cookie_secure())
    return {"ok": True}

@router.get("/auth/options")
def options(svc=Depends(auth_service)): return svc.options()

@router.post("/auth/password-reset")
def request_reset(body: ResetRequest, svc=Depends(auth_service)): return svc.request_reset(body.email)

@router.post("/auth/password-reset/confirm")
def confirm_reset(body: ResetConfirm, svc=Depends(auth_service)): return svc.confirm_reset(body.token, body.password)

@router.post("/admin/users/{target}/password-reset")
def admin_reset_link(target: str, user=Depends(need(P.USERS_MANAGE)), svc=Depends(auth_service)):
    return svc.admin_reset_link(user["id"], target)

@router.get("/me")
def me(user=Depends(current_user)): return user
