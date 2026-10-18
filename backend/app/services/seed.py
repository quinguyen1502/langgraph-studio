"""Startup bootstrap: migrate the schema, seed the demo user (not in production, TASK-0045) and the shared example workflow."""
import time
from ..core import config, security
from ..core.logging import get_logger
from ..models.database import Database
from ..repositories import UserRepository, WorkflowRepository, RunRepository, WorkflowVersionRepository
from .workflow_service import WorkflowService

log = get_logger("seed")


def bootstrap(db: Database) -> None:
    db.migrate()
    users, wfs = UserRepository(db), WorkflowRepository(db)
    u = users.get_by_email(config.DEMO_EMAIL)
    uid = u.id if u else "admin"
    if not u and config.demo_user():  # TASK-0045: no account with a published password in production
        users.add(uid, config.DEMO_EMAIL, security.hash_password(config.DEMO_PASSWORD), time.time())
        users.set_admin(uid)  # the first account administers the studio
    elif u and not config.demo_user() and u.active and security.verify_password(config.DEMO_PASSWORD, u.password or ""):
        users.set_active(u.id, False)
        log.error("%s still has the demo password; it is deactivated in production. Set STUDIO_ADMIN_EMAILS to bootstrap an admin.", config.DEMO_EMAIL)
    if users.count_active_admins() == 0:  # bootstrap / lockout recovery only (TASK-0014): roles are managed in Settings → Users
        for email in config.admin_emails():  # STUDIO_ADMIN_EMAILS
            if (a := users.get_by_email(email)) is not None: users.set_admin(a.id); users.set_active(a.id, True)
        if users.count_active_admins() == 0 and not config.IS_PROD: users.set_admin(uid); users.set_active(uid, True)  # dev: the demo user
    if not users.get_by_id(uid):  # production without the demo user: the oldest active admin owns legacy rows and the example
        uid = next((x.id for x, _ in users.list_all() if x.role == "admin" and x.active), None)
        if uid is None: return
    wfs.adopt_unowned(uid)  # legacy rows created before multi-user support
    if not wfs.exists("example"):
        WorkflowService(wfs, RunRepository(db), WorkflowVersionRepository(db)).seed_example(uid, "example")
