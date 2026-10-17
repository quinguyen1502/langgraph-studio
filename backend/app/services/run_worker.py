"""Executes queued run jobs (TASK-0007). Runs inside the API process (STUDIO_WORKER=1, default) and/or
as a dedicated process (`python -m app.worker`). Uses the same RunService.execute as the WebSocket."""
import asyncio, time
from typing import Callable, Optional
import httpx
from ..core.errors import AppError
from ..core.logging import get_logger
from .job_queue import JobQueue
from .run_service import RunService, error_event
from .trigger_service import run_result

log = get_logger("worker")
CALLBACK_ATTEMPTS = 2


def http_client() -> httpx.Client:
    """Factory for result-webhook calls (tests replace it with a MockTransport client)."""
    return httpx.Client(timeout=10)


def deliver(url: str, payload: dict) -> bool:
    """POST the run result to the caller's webhook; one retry. Never raises."""
    for attempt in range(CALLBACK_ATTEMPTS):
        try:
            with http_client() as c:
                r = c.post(url, json=payload, headers={"X-Studio-Event": "run.finished"})
            if r.status_code < 400: return True
            log.warning("callback %s returned HTTP %s", url, r.status_code)
        except httpx.HTTPError as e:
            log.warning("callback %s failed: %s", url, type(e).__name__)
        if attempt + 1 < CALLBACK_ATTEMPTS: time.sleep(1)
    return False


class RunWorker:
    def __init__(self, jobs: JobQueue, services: Callable[[], RunService]):
        self.jobs, self.services = jobs, services
        self._tasks: list[asyncio.Task] = []; self._stop = False

    async def run_job(self, job: dict) -> Optional[str]:
        svc = self.services(); rid = job["run_id"]; row = svc.runs.get(rid)
        if row is None or row.status != "queued": return None  # cancelled before it started
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
            await asyncio.to_thread(deliver, job["callback_url"], run_result(svc.runs.get(rid)))
        return status

    async def loop(self) -> None:
        while not self._stop:
            try:
                job = await asyncio.to_thread(self.jobs.dequeue, 1.0)
                if job: await self.run_job(job)
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("run job failed"); await asyncio.sleep(1)

    def start(self, n: int) -> None:
        self._stop = False; self._tasks = [asyncio.create_task(self.loop()) for _ in range(n)]

    async def stop(self) -> None:
        self._stop = True
        for t in self._tasks: t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
