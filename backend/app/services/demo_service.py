"""Public demo mode (STUDIO_DEMO_MODE=true; docs/deploy/demo.md).

Design: every visitor signs in to one shared account, DEMO_VISITOR_EMAIL, whose global role is viewer. RBAC already keeps
a viewer away from credentials, knowledge bases, API tokens, MCP servers, workflow creation and every admin page; demo mode
adds the rest:
- refuses(): the API refuses every write from the visitor except signing in/out, cancelling a run, answering a Human node,
  marking notifications read and starting or deleting their own chats in the Chat panel, so nobody can save, share or change the account (password, preferences, identities);
  sign-up and password reset are closed to everyone (DEMO_READ_ONLY).
- the visitor may run unsaved edits (run_service); the engine turns off Code, HTTP Tool and Send email nodes and runs LLM
  and Decision nodes on the offline mock model, so nothing leaves the server.
- check_run(): at most STUDIO_DEMO_RUN_RATE_LIMIT runs per client IP and minute.
- seed(): the visitor and the sample workflows (shared with the visitor as viewer; chat turned on for the Chatbot) exist
  after every boot, since the free
  plan's SQLite file is wiped when the service sleeps.
The admin (STUDIO_ADMIN_EMAILS + STUDIO_ADMIN_PASSWORD) is a normal account and is not restricted."""
import re, time
from typing import Optional
from ..core import config, security
from ..core.errors import AppError
from ..core.logging import get_logger
from ..engine.examples import EXAMPLE
from ..engine.templates import BUILTINS
from ..models.database import Database
from ..models.workflow_share import WorkflowShare
from ..repositories import ChatMessageRepository, ChatSessionRepository, ChatTriggerRepository, RunRepository, UserRepository, WorkflowRepository, WorkflowShareRepository, WorkflowVersionRepository
from .rate_limit import RateLimiter

log = get_logger("demo")
VISITOR_ID = "demo-visitor"
VISITOR_EMAIL, VISITOR_PASSWORD = "demo@superstep.dev", "superstep-demo-2026"  # public on purpose: printed on the sign-in page
SAMPLES = ("builtin-chatbot", "builtin-router", "builtin-approval")  # the chat-enabled Chatbot first
CHAT_SAMPLE = "demo-chatbot"  # web chat on, so the Chat panel works for the visitor
_VISITOR_WRITES = re.compile(r"/api/(auth/(login|logout)|runs/[^/]+/cancel|notifications/(read-all|[^/]+/read)|approvals/inbox/[^/]+"
                             r"|workflows/[^/]+/chat/sessions|chat/sessions/[^/]+)")  # + their own chat sessions (Chat panel)
_CLOSED = re.compile(r"/api/auth/(register|password-reset(/confirm)?)")
UNSAFE = ("POST", "PUT", "PATCH", "DELETE")


def refuses(method: str, path: str, uid: Optional[str]) -> bool:
    """True when demo mode refuses this HTTP request (DEMO_READ_ONLY). Reads are always let through."""
    if method.upper() not in UNSAFE: return False
    if _CLOSED.fullmatch(path): return True
    return uid == VISITOR_ID and not _VISITOR_WRITES.fullmatch(path)


def options() -> dict:
    """What the sign-in page needs to offer "Try the demo"."""
    return {"email": VISITOR_EMAIL, "password": VISITOR_PASSWORD}


class DemoService:
    def __init__(self, limiter: Optional[RateLimiter] = None): self.limiter = limiter

    async def check_run(self, ip: str) -> None:
        limit = config.demo_run_rate_limit()
        if self.limiter is None or not limit: return
        ok, retry = await self.limiter.hit(f"demo-run:{ip}", limit, 60)
        if not ok: raise AppError("RATE_LIMITED", headers={"Retry-After": str(retry)}, retry_after=retry)


def seed(db: Database, owner: str) -> None:
    """Idempotent: the visitor account (viewer, the public password) and the samples owned by `owner` (an admin)."""
    from .workflow_service import WorkflowService
    from .chat_session_service import ChatSessionService
    users, wfs, shares = UserRepository(db), WorkflowRepository(db), WorkflowShareRepository(db)
    triggers = ChatTriggerRepository(db)
    chats = ChatSessionService(ChatSessionRepository(db), triggers, ChatMessageRepository(db), wfs, RunRepository(db))
    if users.get_by_id(VISITOR_ID) is None:
        users.add(VISITOR_ID, VISITOR_EMAIL, security.hash_password(VISITOR_PASSWORD), time.time())
    users.set_role(VISITOR_ID, "viewer"); users.set_active(VISITOR_ID, True)
    svc = WorkflowService(wfs, RunRepository(db), WorkflowVersionRepository(db))
    samples = [("example", dict(EXAMPLE))] + [(f"demo-{t['id'].removeprefix('builtin-')}", {**t["workflow"], "name": t["name"]})
                                             for sid in SAMPLES for t in BUILTINS if t["id"] == sid]
    for wid, wf in samples:
        if not wfs.exists(wid): svc.seed(owner, wid, wf)
        if wid == CHAT_SAMPLE and triggers.web(wid) is None: chats.save_settings(wid, owner, {"enabled": True})
        if shares.role_of(wid, VISITOR_ID) is None:
            shares.upsert(WorkflowShare(workflow_id=wid, user_id=VISITOR_ID, role="viewer", created=time.time(), shared_by=owner))
    log.info("Demo mode: %d sample workflows shared with %s", len(samples), VISITOR_EMAIL)
