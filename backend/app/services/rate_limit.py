"""Fixed-window rate limiter (TASK-0019). Redis (shared by all processes, async client so the event loop
never blocks) when REDIS_URL is set, otherwise in-memory (single process)."""
import asyncio, math, time
from .redis_async import async_redis
from typing import Optional, Protocol

PREFIX = "studio:rl:"


class RateLimiter(Protocol):
    kind: str
    async def hit(self, key: str, limit: int, window: int) -> tuple[bool, int]: ...  # (allowed, retry_after_s)


def _window(window: int, now: float) -> tuple[int, int]:
    start = int(now // window) * window
    return start, max(1, math.ceil(start + window - now))


class InMemoryRateLimiter:
    kind = "memory"
    def __init__(self): self._counts: dict[str, tuple[int, int]] = {}; self._lock = asyncio.Lock()
    async def hit(self, key, limit, window):
        start, retry = _window(window, time.time())
        async with self._lock:
            w, n = self._counts.get(key, (start, 0))
            n = n + 1 if w == start else 1
            self._counts[key] = (start, n)
        return (n <= limit, 0 if n <= limit else retry)


class RedisRateLimiter:
    kind = "redis"
    def __init__(self, url: str, client=None):
        self.url, self._client = url, client
    def _r(self):
        return self._client or async_redis(self.url)
    async def hit(self, key, limit, window):
        start, retry = _window(window, time.time())
        k = f"{PREFIX}{key}:{start}"; r = self._r()
        async with r.pipeline(transaction=True) as p:
            n, _ = await p.incr(k).expire(k, window + 1).execute()
        return (n <= limit, 0 if n <= limit else retry)


def make_rate_limiter(url: Optional[str]) -> RateLimiter:
    return RedisRateLimiter(url) if url else InMemoryRateLimiter()
