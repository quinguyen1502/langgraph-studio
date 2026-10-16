"""Translate domain errors and request validation errors into HTTP responses."""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from ..core.errors import DomainError


def _loc(err) -> str:
    return ".".join(str(x) for x in err.get("loc", []) if x != "body") or "body"


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def domain_error(_: Request, exc: DomainError):
        return JSONResponse(status_code=exc.status, content={"detail": exc.message}, headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def readable_422(_: Request, exc: RequestValidationError):
        errs = [f"{_loc(e)}: {e.get('msg')}" for e in exc.errors()][:10]
        return JSONResponse(status_code=422, content={"detail": "Dữ liệu không hợp lệ — " + "; ".join(errs), "errors": errs})
