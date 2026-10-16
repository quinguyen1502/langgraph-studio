"""Run bus: cross-process run registry, cancel signalling and event fan-out (TASK-0009).

One small interface, two implementations (KISS):
- InMemoryRunBus: default when REDIS_URL is unset (single API process, dev/tests).
- RedisRunBus: REDIS_URL set; lets any API worker cancel a run started on another worker
  and publishes every run event on the `run:{id}:events` channel for observers.
"""
import json, threading
from typing import Callable, Optional, Protocol

KEY_TTL = 24 * 3600  # registry/cancel keys expire even if a worker dies mid-run


class RunBus(Protocol):
    kind: str
    def start(self, rid: str, owner: str) -> None: ...
    def finish(self, rid: str) -> None: ...
    def owner(self, rid: str) -> Optional[str]: ...
    def request_cancel(self, rid: str) -> None: ...
    def is_cancelled(self, rid: str) -> bool: ...
    def publish(self, rid: str, event: dict) -> None: ...
    def ping(self) -> bool: ...


def channel(rid: str) -> str: return f"run:{rid}:events"


class InMemoryRunBus:
    kind = "memory"

    def __init__(self):
        self._owners: dict[str, str] = {}; self._cancelled: set[str] = set(); self._lock = threading.Lock()
        self.listeners: list[Callable[[str, dict], None]] = []  # in-process subscribers (tests, future SSE)

    def start(self, rid, owner):
        with self._lock: self._owners[rid] = owner; self._cancelled.discard(rid)
    def finish(self, rid):
        with self._lock: self._owners.pop(rid, None); self._cancelled.discard(rid)
    def owner(self, rid): return self._owners.get(rid)
    def request_cancel(self, rid):
        with self._lock: self._cancelled.add(rid)
    def is_cancelled(self, rid): return rid in self._cancelled
    def publish(self, rid, event):
        for fn in list(self.listeners): fn(rid, event)
    def ping(self): return True


class RedisRunBus:
    kind = "redis"

    def __init__(self, url: str, client=None):
        if client is None:
            import redis
            client = redis.Redis.from_url(url, decode_responses=True, socket_connect_timeout=2, socket_timeout=2)
        self.r = client

    def start(self, rid, owner):
        p = self.r.pipeline(); p.set(f"run:{rid}:owner", owner, ex=KEY_TTL); p.delete(f"run:{rid}:cancel"); p.execute()
    def finish(self, rid): self.r.delete(f"run:{rid}:owner", f"run:{rid}:cancel")
    def owner(self, rid): return self.r.get(f"run:{rid}:owner")
    def request_cancel(self, rid): self.r.set(f"run:{rid}:cancel", "1", ex=KEY_TTL)
    def is_cancelled(self, rid): return bool(self.r.exists(f"run:{rid}:cancel"))
    def publish(self, rid, event): self.r.publish(channel(rid), json.dumps(event, ensure_ascii=False, default=str))
    def ping(self):
        try: return bool(self.r.ping())
        except Exception: return False


def make_run_bus(url: Optional[str]) -> RunBus:
    return RedisRunBus(url) if url else InMemoryRunBus()
