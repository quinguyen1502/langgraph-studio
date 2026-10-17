"""Run job queue (TASK-0007, DEC-0014; reliable delivery in TASK-0019, DEC-0016).

- InMemoryJobQueue (REDIS_URL unset): **dev/single-process only**. Jobs live in the API process and are lost
  on restart (their runs stay `queued`).
- RedisJobQueue (REDIS_URL set): reliable queue.
  - `dequeue` atomically moves a job from `studio:run-jobs` into this worker's processing list
    `studio:run-jobs:processing:<worker id>` (BLMOVE).
  - `ack` removes the job from that list once the run is recorded.
  - Each worker refreshes a heartbeat key `studio:worker:<id>` (TTL HEARTBEAT_TTL).
  - On start, `recover_stale` moves jobs from processing lists of workers whose heartbeat expired back to the
    queue, marked `recovered` so the run is re-executed from the start.
A job is a small JSON dict: {"run_id", "workflow_id", "owner", "input", "callback_url"?, "token_id"?}.
Blocking calls are made from worker threads (asyncio.to_thread), never on the event loop.
"""
import json, queue, uuid
from typing import Optional, Protocol

QUEUE_KEY = "studio:run-jobs"
PROCESSING_PREFIX = "studio:run-jobs:processing:"
HEARTBEAT_PREFIX = "studio:worker:"
HEARTBEAT_TTL = 30  # seconds; a worker refreshes it every few seconds


class JobQueue(Protocol):
    kind: str
    worker_id: str
    def enqueue(self, job: dict) -> None: ...
    def dequeue(self, timeout: float) -> Optional[dict]: ...  # blocking, returns None on timeout
    def ack(self, job: dict) -> None: ...
    def heartbeat(self) -> None: ...
    def recover_stale(self) -> int: ...


class InMemoryJobQueue:
    kind = "memory"
    def __init__(self): self._q: "queue.Queue[dict]" = queue.Queue(); self.worker_id = "local"
    def enqueue(self, job): self._q.put(dict(job))
    def dequeue(self, timeout):
        try: return self._q.get(timeout=timeout)
        except queue.Empty: return None
    def ack(self, job): pass
    def heartbeat(self): pass
    def recover_stale(self): return 0


class RedisJobQueue:
    kind = "redis"
    def __init__(self, url: str, client=None, worker_id: Optional[str] = None):
        if client is None:
            import redis
            client = redis.Redis.from_url(url, decode_responses=True, socket_connect_timeout=2, socket_timeout=10)
        self.r = client; self.worker_id = worker_id or uuid.uuid4().hex[:12]
        self.processing = PROCESSING_PREFIX + self.worker_id

    def enqueue(self, job): self.r.lpush(QUEUE_KEY, json.dumps(job, ensure_ascii=False))

    def dequeue(self, timeout):
        raw = self.r.blmove(QUEUE_KEY, self.processing, max(1, int(timeout)), "RIGHT", "LEFT")
        if raw is None: return None
        job = json.loads(raw); job["_raw"] = raw  # exact payload, needed for LREM on ack
        return job

    def ack(self, job):
        raw = job.get("_raw")
        if raw: self.r.lrem(self.processing, 1, raw)

    def heartbeat(self): self.r.set(HEARTBEAT_PREFIX + self.worker_id, "1", ex=HEARTBEAT_TTL)

    def recover_stale(self) -> int:
        """Requeue jobs held by workers that are gone (no heartbeat). Safe to run on every worker start."""
        n = 0
        for key in self.r.scan_iter(match=PROCESSING_PREFIX + "*"):
            wid = key[len(PROCESSING_PREFIX):]
            if wid == self.worker_id or self.r.exists(HEARTBEAT_PREFIX + wid): continue
            while (raw := self.r.rpop(key)) is not None:
                job = json.loads(raw); job["recovered"] = True
                self.r.rpush(QUEUE_KEY, json.dumps(job, ensure_ascii=False)); n += 1  # RPUSH: served next (BLMOVE takes from the right)
        return n


def make_job_queue(url: Optional[str]) -> JobQueue:
    return RedisJobQueue(url) if url else InMemoryJobQueue()
