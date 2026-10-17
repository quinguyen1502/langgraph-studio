"""App factory. `app.main:app` stays the uvicorn entrypoint."""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.deps import get_db, run_service, run_worker
from .core.logging import get_logger
from .core import config
from .api.error_handlers import register_error_handlers
from .api.routes import ROUTERS
from .core.security import check_secret
from .schemas.envelope import EnvelopeResponse
from .services.seed import bootstrap


SWEEP_EVERY = 60  # seconds


async def expire_waiting_loop() -> None:
    while True:
        try: await asyncio.to_thread(run_service().expire_waiting)
        except asyncio.CancelledError: raise
        except Exception: get_logger("sweeper").exception("expiring waiting runs failed")
        await asyncio.sleep(SWEEP_EVERY)


def create_app() -> FastAPI:
    check_secret()
    bootstrap(get_db())  # alembic upgrade head + demo user + example workflow
    @asynccontextmanager
    async def lifespan(_app):
        w = run_worker() if config.worker_enabled() else None  # executes queued API runs (TASK-0007)
        if w: w.start(config.worker_concurrency())
        sweeper = asyncio.create_task(expire_waiting_loop())  # TASK-0019: waiting runs past STUDIO_WAIT_TTL -> expired
        yield
        sweeper.cancel()
        if w: await w.stop()

    app = FastAPI(title="LangGraph Studio MVP", default_response_class=EnvelopeResponse, lifespan=lifespan)  # every REST response is an envelope
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    register_error_handlers(app)
    for r in ROUTERS: app.include_router(r)
    return app


app = create_app()
