"""FastAPI dependency wiring: one Database per process, services built per request (cheap)."""
from functools import lru_cache
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from ..core import config
from ..core.errors import AppError
from ..models.database import Database
from ..repositories import CredentialRepository, RunRepository, UserRepository, WorkflowRepository
from ..services.auth_service import AuthService
from ..services.credential_service import CredentialService
from ..services.import_service import ImportService
from ..services.run_bus import RunBus, make_run_bus
from ..services.run_service import RunService
from ..services.telemetry import Telemetry
from ..services.workflow_service import WorkflowService


@lru_cache
def get_db() -> Database:
    return Database()


@lru_cache
def get_run_bus() -> RunBus:
    return make_run_bus(config.REDIS_URL)  # Redis when REDIS_URL is set, else in-memory


@lru_cache
def get_telemetry() -> Telemetry:
    return Telemetry()  # exporters from OTEL_* / LANGSMITH_* env; no-op when none


def workflow_service() -> WorkflowService:
    db = get_db(); return WorkflowService(WorkflowRepository(db), RunRepository(db))

def auth_service() -> AuthService:
    return AuthService(UserRepository(get_db()), workflow_service())

def run_service() -> RunService:
    db = get_db(); return RunService(WorkflowRepository(db), RunRepository(db), credential_service(), get_run_bus(), get_telemetry())

def credential_service() -> CredentialService:
    return CredentialService(CredentialRepository(get_db()))

def import_service() -> ImportService:
    return ImportService(workflow_service())


bearer = HTTPBearer(auto_error=False)

def current_user(cred: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict:
    return AuthService.user_from_token(cred.credentials if cred else None)


async def limit_body(request: Request):
    n = int(request.headers.get("content-length") or 0)
    if n > config.workflow_max(): raise AppError("WORKFLOW_TOO_LARGE", max_kb=config.workflow_max() // 1024)
