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
    if not u or not config.IS_PROD: users.set_admin(uid)  # the demo user manages org-wide approval channels (dev)
    for email in config.admin_emails():  # STUDIO_ADMIN_EMAILS (TASK-0022 follow-up)
        if (a := users.get_by_email(email)) is not None and not a.is_admin: users.set_admin(a.id)
    wfs.adopt_unowned(uid)  # legacy rows created before multi-user support
    if not wfs.exists("example"):
        WorkflowService(wfs, RunRepository(db), WorkflowVersionRepository(db)).seed_example(uid, "example")
