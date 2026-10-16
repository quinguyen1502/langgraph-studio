"""Run job queue (TASK-0007, DEC-0014): runs started without a WebSocket (REST/webhook triggers).

One small interface, two implementations (same pattern as RunBus):
- InMemoryJobQueue when REDIS_URL is unset: jobs are executed by the worker inside the API process.
- RedisJobQueue when REDIS_URL is set: a Redis list (LPUSH / BRPOP), so any API process or a dedicated
  `python -m app.worker` process can execute them.
A job is a small JSON dict: {"run_id", "workflow_id", "owner", "input", "callback_url"?}.
"""
import json, queue
from typing import Optional, Protocol

QUEUE_KEY = "studio:run-jobs"


class JobQueue(Protocol):
    kind: str
    def enqueue(self, job: dict) -> None: ...
    def dequeue(self, timeout: float) -> Optional[dict]: ...  # blocking, returns None on timeout


class InMemoryJobQueue:
    kind = "memory"
    def __init__(self): self._q: "queue.Queue[dict]" = queue.Queue()
    def enqueue(self, job): self._q.put(dict(job))
    def dequeue(self, timeout):
        try: return self._q.get(timeout=timeout)
        except queue.Empty: return None


class RedisJobQueue:
    kind = "redis"
    def __init__(self, url: str, client=None):
        if client is None:
            import redis
            client = redis.Redis.from_url(url, decode_responses=True, socket_connect_timeout=2)
        self.r = client
    def enqueue(self, job): self.r.lpush(QUEUE_KEY, json.dumps(job, ensure_ascii=False))
    def dequeue(self, timeout):
        item = self.r.brpop(QUEUE_KEY, timeout=max(1, int(timeout)))
        return json.loads(item[1]) if item else None


def make_job_queue(url: Optional[str]) -> JobQueue:
    return RedisJobQueue(url) if url else InMemoryJobQueue()
