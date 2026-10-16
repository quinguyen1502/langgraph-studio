"""Startup bootstrap: migrate the schema, seed the demo user and the shared example workflow."""
import time
from ..core import config, security
from ..models.database import Database
from ..repositories import UserRepository, WorkflowRepository, RunRepository, WorkflowVersionRepository
from .workflow_service import WorkflowService


def bootstrap(db: Database) -> None:
    db.migrate()
    users, wfs = UserRepository(db), WorkflowRepository(db)
    u = users.get_by_email(config.DEMO_EMAIL)
    uid = u.id if u else "admin"
    if not u:
        users.add(uid, config.DEMO_EMAIL, security.hash_password(config.DEMO_PASSWORD), time.time())
    wfs.adopt_unowned(uid)  # legacy rows created before multi-user support
    if not wfs.exists("example"):
        WorkflowService(wfs, RunRepository(db), WorkflowVersionRepository(db)).seed_example(uid, "example")
