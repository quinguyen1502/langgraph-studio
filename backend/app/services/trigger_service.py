"""API / webhook triggers (TASK-0007): per-workflow tokens, queued runs, sync wait, result callbacks."""
import asyncio, hashlib, json, secrets, time, uuid
from typing import Optional
from ..core import config, crypto
from ..core.errors import AppError
from ..core.logging import get_logger
from ..engine.limits import size
from ..models import Run, WorkflowToken
from ..repositories import RunRepository, WorkflowRepository, WorkflowTokenRepository
from .job_queue import JobQueue
from .rate_limit import RateLimiter
from .telemetry import trace_url
from .webhooks import check_callback_url  # noqa: F401  (re-exported)

log = get_logger("triggers")
TOKEN_PREFIX = "wft_"
SECRET_PREFIX = "whsec_"
FINAL = ("ok", "error", "cancelled", "timeout", "waiting", "expired")


def _hash(token: str) -> str: return hashlib.sha256(token.encode()).hexdigest()


class TriggerService:
    def __init__(self, workflows: WorkflowRepository, runs: RunRepository, tokens: WorkflowTokenRepository, jobs: JobQueue,
                 limiter: Optional[RateLimiter] = None):
        self.workflows, self.runs, self.tokens, self.jobs, self.limiter = workflows, runs, tokens, jobs, limiter

    # ---- token management (owner, JWT) ----
    def _owned(self, wid: str, uid: str):
        if self.workflows.get_owned(wid, uid) is None: raise AppError("WORKFLOW_NOT_FOUND")

    @staticmethod
    def _public(t: WorkflowToken) -> dict:
        return {"id": t.id, "name": t.name, "prefix": t.prefix, "created": t.created, "last_used": t.last_used, "revoked": t.revoked}

    def list_tokens(self, wid: str, uid: str) -> list[dict]:
        self._owned(wid, uid); return [self._public(t) for t in self.tokens.list_for_workflow(wid)]

    def create_token(self, wid: str, uid: str, name: str) -> dict:
        """Returns the plaintext token and webhook signing secret once. The token is stored as a hash; the
        signing secret is encrypted (the server needs it to sign callbacks)."""
        self._owned(wid, uid)
        secret = TOKEN_PREFIX + secrets.token_urlsafe(24); signing = SECRET_PREFIX + secrets.token_urlsafe(24)
        t = self.tokens.add(WorkflowToken(id=uuid.uuid4().hex[:10], workflow_id=wid, owner=uid, name=(name or "API token").strip()[:80],
                                          token_hash=_hash(secret), prefix=secret[:10], created=time.time(), signing_secret=crypto.encrypt(signing)))
        return {**self._public(t), "token": secret, "signing_secret": signing}

    def signing_secret(self, tid: Optional[str]) -> Optional[str]:
        """Decrypted webhook signing secret of a token (None for tokens created before TASK-0019)."""
        t = self.tokens.get(tid) if tid else None
        return crypto.decrypt(t.signing_secret) if t and t.signing_secret else None

    def revoke_token(self, wid: str, tid: str, uid: str) -> dict:
        self._owned(wid, uid); t = self.tokens.get(tid)
        if t is None or t.workflow_id != wid: raise AppError("TOKEN_NOT_FOUND")
        if not t.revoked: self.tokens.set_fields(tid, revoked=time.time())
        return {"ok": True}

    # ---- trigger (workflow token) ----
    def authenticate(self, wid: str, token: Optional[str]) -> WorkflowToken:
        """Valid, not revoked, for this workflow, and the workflow still belongs to the token's owner."""
        t = self.tokens.by_hash(_hash(token)) if token and token.startswith(TOKEN_PREFIX) else None
        if t is None or t.revoked or t.workflow_id != wid or self.workflows.get_owned(wid, t.owner) is None:
            raise AppError("TRIGGER_TOKEN_INVALID")
        self.tokens.set_fields(t.id, last_used=time.time())
        return t

    async def check_rate(self, tok: WorkflowToken) -> None:
        """Per-token fixed-window limit on starting runs (STUDIO_TRIGGER_RATE_LIMIT per STUDIO_TRIGGER_RATE_WINDOW s)."""
        limit = config.trigger_rate_limit()
        if self.limiter is None or not limit: return
        ok, retry = await self.limiter.hit(f"token:{tok.id}", limit, config.trigger_rate_window())
        if not ok: raise AppError("RATE_LIMITED", headers={"Retry-After": str(retry)}, retry_after=retry)

    def start(self, tok: WorkflowToken, inp, callback_url: Optional[str]) -> str:
        if not isinstance(inp, dict): raise AppError("RUN_INPUT_INVALID")
        if size(inp) > config.input_max(): raise AppError("RUN_INPUT_TOO_LARGE", max_kb=config.input_max() // 1024)
        callback_url = check_callback_url(callback_url)
        rid = uuid.uuid4().hex[:10]
        self.runs.add(Run(id=rid, workflow_id=tok.workflow_id, input=json.dumps(inp, ensure_ascii=False), events="[]", status="queued",
                          started=time.time(), owner=tok.owner, source="api"))
        self.jobs.enqueue({"run_id": rid, "workflow_id": tok.workflow_id, "owner": tok.owner, "input": inp, "callback_url": callback_url, "token_id": tok.id})
        return rid

    def result(self, tok: WorkflowToken, rid: str) -> dict:
        r = self.runs.get(rid)
        if r is None or r.workflow_id != tok.workflow_id or r.owner != tok.owner: raise AppError("RUN_NOT_FOUND")
        return run_result(r)

    async def wait(self, tok: WorkflowToken, rid: str, timeout: float) -> dict:
        """Sync mode: poll the shared runs table (works across worker processes) until the run settles."""
        deadline = time.time() + timeout
        while True:
            res = await asyncio.to_thread(self.result, tok, rid)
            if res["status"] in FINAL or time.time() >= deadline: return res
            await asyncio.sleep(0.2)


def run_result(r: Run) -> dict:
    """Public result of an API-triggered run (REST response and webhook body)."""
    done = r.status in FINAL
    events = json.loads(r.events or "[]") if done else []
    err = next((e.get("error") for e in reversed(events) if e.get("type") == "error"), None)
    wait = next((e for e in reversed(events) if e.get("type") == "run_waiting"), None) if r.status == "waiting" else None
    return {"run_id": r.id, "workflow_id": r.workflow_id, "status": r.status, "source": r.source or "ui",
            "final_state": json.loads(r.final_state or "null") if done else None, "error": err,
            "waiting": {"node": wait.get("node"), "prompt": wait.get("prompt")} if wait else None,
            "metrics": None if r.duration_ms is None else {"duration_ms": r.duration_ms, "tokens_in": r.tokens_in, "tokens_out": r.tokens_out,
                                                           "cost_usd": r.cost_usd, "error_count": r.error_count},
            "trace_url": trace_url(r.trace_id), "started": r.started, "ended": r.ended if done else None}
