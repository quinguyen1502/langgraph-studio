"""Dedicated run worker process: `python -m app.worker` (needs REDIS_URL so jobs are shared with the API)."""
import asyncio
from .api.deps import get_db, run_service, run_worker
from .core import config
from .core.logging import get_logger
from .services.seed import bootstrap


async def main() -> None:
    bootstrap(get_db())
    w = run_worker(); w.start(config.worker_concurrency())
    get_logger("worker").info("worker started (%s queue, concurrency %s)", w.jobs.kind, config.worker_concurrency())
    await asyncio.gather(*w._tasks)


if __name__ == "__main__":
    asyncio.run(main())
