"""Executes queued run jobs (TASK-0007). Runs inside the API process (STUDIO_WORKER=1, default) and/or
as a dedicated process (`python -m app.worker`). Uses the same RunService.execute as the WebSocket."""
import asyncio, time
from typing import Callable, Optional
from ..core.errors import AppError
from ..core.logging import get_logger
from .job_queue import JobQueue
from .run_service import RunService, error_event
from .trigger_service import run_result
from . import webhooks

log = get_logger("worker")
HEARTBEAT_EVERY = 10  # seconds (< job_queue.HEARTBEAT_TTL)


class RunWorker:
    def __init__(self, jobs: JobQueue, services: Callable[[], RunService], secrets: Optional[Callable[[str], Optional[str]]] = None):
        self.jobs, self.services, self.secrets = jobs, services, secrets  # secrets: token id -> webhook signing secret
        self._tasks: list[asyncio.Task] = []; self._stop = False

    async def run_job(self, job: dict) -> Optional[str]:
        svc = self.services(); rid = job["run_id"]; row = svc.runs.get(rid)
        # skip cancelled/finished jobs; a recovered job (its worker died mid-run) is re-executed from the start
        if row is None or not (row.status == "queued" or (row.status == "running" and job.get("recovered"))): return None
        svc.runs.set_status(rid, "running")
        try:
            plan = svc.plan(job["owner"], {"workflow_id": job["workflow_id"], "input": job.get("input") or {}})
            plan.run_id, plan.source = rid, "api"
            async def send(ev): return True                       # nobody streams; history + webhook carry the result
            async def listen(): await asyncio.Event().wait()      # cancel arrives through the RunBus
            status = await svc.execute(plan, send, listen, job["owner"])
        except AppError as e:  # e.g. the workflow was deleted or is too large
            svc.record(rid, job["workflow_id"], job.get("input") or {}, [error_event(e.to_dict())], None, "error", row.started, job["owner"], source="api")
            status = "error"
        if job.get("callback_url"):
            secret = self.secrets(job.get("token_id")) if self.secrets else None
            await asyncio.to_thread(webhooks.deliver, job["callback_url"], run_result(svc.runs.get(rid)), secret)
        return status

    async def loop(self) -> None:
        while not self._stop:
            try:
                job = await asyncio.to_thread(self.jobs.dequeue, 1.0)
                if job:
                    try: await self.run_job(job)
                    finally: await asyncio.to_thread(self.jobs.ack, job)  # recorded (or skipped): drop from processing list
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("run job failed"); await asyncio.sleep(1)

    async def beat(self) -> None:
        while not self._stop:
            try: await asyncio.to_thread(self.jobs.heartbeat)
            except Exception: log.warning("worker heartbeat failed")
            await asyncio.sleep(HEARTBEAT_EVERY)

    async def recover(self) -> int:
        try:
            n = await asyncio.to_thread(self.jobs.recover_stale)
            if n: log.warning("requeued %s job(s) from dead workers", n)
            return n
        except Exception:
            log.exception("recovering stale jobs failed"); return 0

    def start(self, n: int) -> None:
        self._stop = False
        async def boot():
            await asyncio.to_thread(self.jobs.heartbeat); await self.recover()  # own heartbeat first, then reclaim dead workers' jobs
        self._tasks = [asyncio.create_task(boot()), asyncio.create_task(self.beat())] + [asyncio.create_task(self.loop()) for _ in range(n)]

    async def stop(self) -> None:
        self._stop = True
        for t in self._tasks: t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
