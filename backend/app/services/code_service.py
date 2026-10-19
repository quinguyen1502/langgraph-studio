"""Tool node Code mode for the editor (TASK-0055, DEC-0041): what the server can run, and Test with sample state."""
from __future__ import annotations
import asyncio
from typing import Any, Optional
from ..core import config
from ..core import permissions as P
from ..core.errors import AppError
from ..engine import code_runtime
from .access import AccessService
from .rate_limit import RateLimiter


class CodeService:
    def __init__(self, access: AccessService, limiter: RateLimiter):
        self.access, self.limiter = access, limiter

    def runtime(self) -> dict:
        """The one source the UI reads for the Code mode: runtime, whether it can run now, image, limits and packages."""
        why = code_runtime.unavailable()
        return {"code_runtime": config.code_runtime(), "available": why is None, "problem": None if why in (None, "off") else why,
                "image": config.code_image(), "packages": config.code_packages(), "starter": code_runtime.STARTER,
                "limits": {"memory": config.code_memory(), "cpus": config.code_cpus(), "pids": config.code_pids(),
                           "seconds": config.code_max_seconds(), "source_kb": code_runtime.SOURCE_MAX // 1024}}

    async def test(self, uid: str, source: str, state: Any, node: Optional[str] = None, timeout: Optional[float] = None) -> dict:
        """Run unsaved source once against a sample state. Nothing is stored. A failure of the code itself is a result
        ({ok: false, error, traceback}); a server that cannot run code, or a bad request, is an error."""
        if not self.access.can(uid, P.CODE_WRITE): raise AppError("CODE_WRITE_FORBIDDEN")
        ok, retry = await self.limiter.hit(f"code-test:{uid}", config.code_test_per_minute(), 60)
        if not ok: raise AppError("RATE_LIMITED", headers={"Retry-After": str(retry)}, retry_after=retry)
        if not isinstance(state, dict): state = {}
        try: res = await asyncio.to_thread(code_runtime.run_code, source, state, node=node or "test", timeout=timeout)
        except code_runtime.CodeFailure as e: return {"ok": False, "error": e.to_dict(), **e.output}
        return {"ok": True, "value": res.value, **res.trace()}
