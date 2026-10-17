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
    if not u: users.set_admin(uid)  # the first account administers the studio
    if users.count_active_admins() == 0:  # bootstrap / lockout recovery only (TASK-0014): roles are managed in Settings → Users
        for email in config.admin_emails():  # STUDIO_ADMIN_EMAILS
            if (a := users.get_by_email(email)) is not None: users.set_admin(a.id); users.set_active(a.id, True)
        if users.count_active_admins() == 0 and not config.IS_PROD: users.set_admin(uid); users.set_active(uid, True)  # dev: the demo user
    wfs.adopt_unowned(uid)  # legacy rows created before multi-user support
    if not wfs.exists("example"):
        WorkflowService(wfs, RunRepository(db), WorkflowVersionRepository(db)).seed_example(uid, "example")
