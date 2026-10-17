"""Executes queued jobs (TASK-0007; leases, recovery from checkpoints and webhook deliveries in TASK-0020, DEC-0017).

Runs inside the API process (STUDIO_WORKER=1, default) and/or as a dedicated process (`python -m app.worker`).
- Run jobs use the same RunService.execute as the WebSocket, with progress checkpoints after every node, so a
  job recovered from a dead worker continues from its last finished node instead of starting over.
- Delivery jobs make one webhook attempt (DeliveryService) and reschedule themselves with backoff on failure.
- `maintain` (every worker): promotes due delayed jobs every second and reaps expired leases every
  STUDIO_JOB_REAP_EVERY seconds. The lease of a running job is renewed every visibility/3 seconds.
"""
import asyncio, time
from typing import Callable, Optional
from ..core import config
from ..core.errors import AppError
from ..core.logging import get_logger
from .job_queue import JobQueue
from .run_service import RunService, error_event
from .trigger_service import run_result

log = get_logger("worker")


class RunWorker:
    def __init__(self, jobs: JobQueue, services: Callable[[], RunService], deliveries: Optional[Callable[[], object]] = None):
        self.jobs, self.services, self.deliveries = jobs, services, deliveries  # deliveries: -> DeliveryService
        self._tasks: list[asyncio.Task] = []; self._stop = False

    async def run_job(self, job: dict) -> Optional[str]:
        if job.get("kind") == "delivery":
            return await asyncio.to_thread(self.deliveries().attempt, job["delivery_id"]) if self.deliveries else None
        svc = self.services(); rid = job["run_id"]; row = svc.runs.get(rid)
        # skip cancelled/finished jobs; a recovered job (its worker died mid-run) continues from its checkpoint
        if row is None or not (row.status == "queued" or (row.status == "running" and job.get("recovered"))): return None
        svc.runs.set_status(rid, "running")
        try:
            plan = svc.plan_recover(row) if job.get("recovered") and row.status == "running" else None
            if plan is None:  # fresh job, or recovered before its first checkpoint: (re)start from the beginning
                plan = svc.plan(job["owner"], {"workflow_id": job["workflow_id"], "input": job.get("input") or {}})
                plan.run_id, plan.source, plan.checkpointing = rid, "api", True
            async def send(ev): return True                       # nobody streams; history + webhook carry the result
            async def listen(): await asyncio.Event().wait()      # cancel arrives through the RunBus
            status = await svc.execute(plan, send, listen, job["owner"])
        except AppError as e:  # e.g. the workflow was deleted or is too large
            svc.record(rid, job["workflow_id"], job.get("input") or {}, [error_event(e.to_dict())], None, "error", row.started, job["owner"], source="api")
            status = "error"
        if job.get("callback_url") and self.deliveries:
            r = svc.runs.get(rid)
            await asyncio.to_thread(self.deliveries().create, job["workflow_id"], rid, job.get("token_id"), job["callback_url"], run_result(r))
        return status

    async def _with_lease(self, job: dict) -> None:
        """Run the job while renewing its lease so the reaper leaves it alone."""
        async def renew():
            while True:
                await asyncio.sleep(max(1.0, config.job_visibility() / 3))
                try: await asyncio.to_thread(self.jobs.touch, job)
                except Exception: log.warning("renewing job lease failed")
        keeper = asyncio.create_task(renew())
        try: await self.run_job(job)
        finally:
            keeper.cancel()
            await asyncio.to_thread(self.jobs.ack, job)  # recorded (or skipped): drop from processing list

    async def loop(self) -> None:
        while not self._stop:
            try:
                job = await asyncio.to_thread(self.jobs.dequeue, 1.0)
                if job: await self._with_lease(job)
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("job failed"); await asyncio.sleep(1)

    async def reap(self) -> int:
        try:
            n = await asyncio.to_thread(self.jobs.reap)
            if n: log.warning("requeued %s job(s) whose lease expired", n)
            return n
        except Exception:
            log.exception("reaping expired jobs failed"); return 0

    async def maintain(self) -> None:
        last_reap = 0.0
        while not self._stop:
            try: await asyncio.to_thread(self.jobs.promote_due)
            except Exception: log.warning("promoting delayed jobs failed")
            if time.time() - last_reap >= config.job_reap_every():
                last_reap = time.time(); await self.reap()
            await asyncio.sleep(min(1.0, config.job_reap_every()))

    def start(self, n: int) -> None:
        self._stop = False
        self._tasks = [asyncio.create_task(self.maintain())] + [asyncio.create_task(self.loop()) for _ in range(n)]

    async def stop(self) -> None:
        self._stop = True
        for t in self._tasks: t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
