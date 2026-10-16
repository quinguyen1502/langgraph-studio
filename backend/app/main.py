"""App factory. `app.main:app` stays the uvicorn entrypoint."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.deps import get_db
from .api.error_handlers import register_error_handlers
from .api.routes import ROUTERS
from .core.security import check_secret
from .schemas.envelope import EnvelopeResponse
from .services.seed import bootstrap


def create_app() -> FastAPI:
    check_secret()
    bootstrap(get_db())  # alembic upgrade head + demo user + example workflow
    app = FastAPI(title="LangGraph Studio MVP", default_response_class=EnvelopeResponse)  # every REST response is an envelope
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    register_error_handlers(app)
    for r in ROUTERS: app.include_router(r)
    return app


app = create_app()
