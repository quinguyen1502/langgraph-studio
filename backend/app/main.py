"""App factory. `app.main:app` stays the uvicorn entrypoint."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.deps import get_db, run_worker
from .core import config
from .api.error_handlers import register_error_handlers
from .api.routes import ROUTERS
from .core.security import check_secret
from .schemas.envelope import EnvelopeResponse
from .services.seed import bootstrap


def create_app() -> FastAPI:
    check_secret()
    bootstrap(get_db())  # alembic upgrade head + demo user + example workflow
    @asynccontextmanager
    async def lifespan(_app):
        w = run_worker() if config.worker_enabled() else None  # executes queued API runs (TASK-0007)
        if w: w.start(config.worker_concurrency())
        yield
        if w: await w.stop()

    app = FastAPI(title="LangGraph Studio MVP", default_response_class=EnvelopeResponse, lifespan=lifespan)  # every REST response is an envelope
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    register_error_handlers(app)
    for r in ROUTERS: app.include_router(r)
    return app


app = create_app()
