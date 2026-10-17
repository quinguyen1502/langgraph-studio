"""FastAPI dependency wiring: one Database per process, services built per request (cheap)."""
from functools import lru_cache
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from ..core import config
from ..core.errors import AppError
from ..services.notification_hub import NotificationHub, make_notification_hub
from ..models.database import Database
from ..repositories import CredentialRepository, RunRepository, UserRepository, WorkflowRepository, WorkflowTokenRepository, WorkflowVersionRepository, NotificationRepository, WebhookDeliveryRepository, NodeResultRepository, ApprovalRepository, KnowledgeRepository
from ..services.knowledge_service import KnowledgeService
from ..services.approval_service import ApprovalService
from ..services.identity_service import IdentityService
from ..services.channel_service import ChannelService
from ..services.approval_channels import ADAPTERS
from ..services.auth_service import AuthService
from ..services.credential_service import CredentialService
from ..services.import_service import ImportService
from ..services.run_bus import RunBus, make_run_bus
from ..services.job_queue import JobQueue, make_job_queue
from ..services.run_service import RunService
from ..services.run_worker import RunWorker
from ..services.delivery_service import DeliveryService
from ..services.notification_service import NotificationService
from ..services.rate_limit import RateLimiter, make_rate_limiter
from ..services.trigger_service import TriggerService
from ..services.telemetry import Telemetry
from ..services.workflow_service import WorkflowService


@lru_cache
def get_db() -> Database:
    return Database()


@lru_cache
def get_run_bus() -> RunBus:
    return make_run_bus(config.REDIS_URL)  # Redis when REDIS_URL is set, else in-memory


@lru_cache
def get_job_queue() -> JobQueue:
    return make_job_queue(config.REDIS_URL)  # Redis list when REDIS_URL is set, else in-process


@lru_cache
def run_worker() -> RunWorker:
    return RunWorker(get_job_queue(), run_service, delivery_service)


@lru_cache
def get_rate_limiter() -> RateLimiter:
    return make_rate_limiter(config.REDIS_URL)  # shared via Redis, else per process


def delivery_service() -> DeliveryService:
    db = get_db(); return DeliveryService(WebhookDeliveryRepository(db), WorkflowRepository(db), get_job_queue(), trigger_service().signing_secrets)


@lru_cache
def get_notification_hub() -> NotificationHub:
    return make_notification_hub(config.REDIS_URL)  # Redis pub/sub when REDIS_URL is set, else in-process (TASK-0021)


def notification_service() -> NotificationService:
    db = get_db(); return NotificationService(NotificationRepository(db), UserRepository(db), WorkflowRepository(db), hub=get_notification_hub())


def trigger_service() -> TriggerService:
    db = get_db(); return TriggerService(WorkflowRepository(db), RunRepository(db), WorkflowTokenRepository(db), get_job_queue(), get_rate_limiter())


@lru_cache
def get_telemetry() -> Telemetry:
    return Telemetry()  # exporters from OTEL_* / LANGSMITH_* env; no-op when none


def workflow_service() -> WorkflowService:
    db = get_db(); return WorkflowService(WorkflowRepository(db), RunRepository(db), WorkflowVersionRepository(db))

def auth_service() -> AuthService:
    return AuthService(UserRepository(get_db()), workflow_service())

def run_service() -> RunService:
    db = get_db(); return RunService(WorkflowRepository(db), RunRepository(db), credential_service(), get_run_bus(), get_telemetry(), WorkflowVersionRepository(db), notification_service(), NodeResultRepository(db), approval_service(), delivery_service,
                      knowledge=knowledge_service())

def channel_service() -> ChannelService:
    db = get_db(); return ChannelService(ApprovalRepository(db), UserRepository(db), ADAPTERS)

def approval_service() -> ApprovalService:
    db = get_db(); return ApprovalService(ApprovalRepository(db), UserRepository(db), WorkflowRepository(db), RunRepository(db), channel_service(), get_job_queue().enqueue,
                                         limiter=get_rate_limiter())

def credential_service() -> CredentialService:
    return CredentialService(CredentialRepository(get_db()))

def knowledge_service() -> KnowledgeService:
    return KnowledgeService(KnowledgeRepository(get_db()), credential_service())

def import_service() -> ImportService:
    return ImportService(workflow_service())


bearer = HTTPBearer(auto_error=False)

def current_user(cred: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict:
    return AuthService.user_from_token(cred.credentials if cred else None)


async def limit_body(request: Request):
    n = int(request.headers.get("content-length") or 0)
    if n > config.workflow_max(): raise AppError("WORKFLOW_TOO_LARGE", max_kb=config.workflow_max() // 1024)


def identity_service() -> IdentityService:
    ch = channel_service(); return IdentityService(ch.repo, ch.users, ch)
