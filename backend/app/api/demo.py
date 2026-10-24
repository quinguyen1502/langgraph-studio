"""Demo-mode guard (STUDIO_DEMO_MODE): refuses writes from the shared visitor account before any route runs.
The policy lives in services/demo_service.refuses; this only finds who is asking (no database read needed)."""
from typing import Optional
from fastapi import FastAPI, Request
from ..core import security
from ..core.errors import AppError
from ..services import demo_service
from .error_handlers import respond


def _uid(request: Request) -> Optional[str]:
    auth = request.headers.get("authorization") or ""
    token = auth[7:] if auth.lower().startswith("bearer ") else request.cookies.get(security.SESSION_COOKIE)
    if not token: return None
    try: return security.decode_token(token).get("sub")
    except AppError: return None  # the route itself answers an invalid token


def install_demo_guard(app: FastAPI) -> None:
    @app.middleware("http")
    async def demo_guard(request: Request, call_next):
        if demo_service.refuses(request.method, request.url.path, _uid(request)): return respond(AppError("DEMO_READ_ONLY"))
        return await call_next(request)
