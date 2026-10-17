"""Notifications for runs that need a human (TASK-0020, DEC-0017).

Always: an in-app row (bell in the header, mark read).
Optional channels, each a no-op unless configured:
- E-mail via SMTP (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM, SMTP_STARTTLS / SMTP_SSL).
- A generic notify webhook (STUDIO_NOTIFY_WEBHOOK_URL, signed with STUDIO_NOTIFY_WEBHOOK_SECRET when set; same
  SSRF guard, DNS pinning and signature format as result webhooks).
External channels run in a background thread so recording a run never waits on SMTP/HTTP.
"""
import json, smtplib, ssl, threading, time, uuid
from email.message import EmailMessage
from typing import Optional
from ..core import config
from ..core.errors import AppError
from ..core.logging import get_logger
from ..models import Notification
from ..repositories import NotificationRepository, UserRepository, WorkflowRepository
from . import webhooks

log = get_logger("notify")
KINDS = {"run_waiting": "A run is waiting for your response", "run_expired": "A waiting run expired"}


class NotificationService:
    def __init__(self, repo: NotificationRepository, users: Optional[UserRepository] = None,
                 workflows: Optional[WorkflowRepository] = None, background: bool = True):
        self.repo, self.users, self.workflows, self.background = repo, users, workflows, background

    @staticmethod
    def public(n: Notification) -> dict:
        return {"id": n.id, "kind": n.kind, "run_id": n.run_id, "workflow_id": n.workflow_id, "title": n.title,
                "params": json.loads(n.params or "{}"), "link": n.link, "created": n.created, "read": n.read_at is not None}

    # ---- producer ----
    def run_event(self, kind: str, uid: str, run_id: str, workflow_id: Optional[str], node_event: Optional[dict] = None) -> Notification:
        w = self.workflows.get(workflow_id) if self.workflows and workflow_id and workflow_id != "adhoc" else None
        ev = node_event or {}
        params = {"workflow_name": w.name if w else None, "label": ev.get("label"), "prompt": ev.get("prompt")}
        link = f"/workflows/{workflow_id}?run={run_id}" if workflow_id and workflow_id != "adhoc" else None
        n = self.repo.add(Notification(id=uuid.uuid4().hex[:12], user_id=uid, kind=kind, run_id=run_id, workflow_id=workflow_id,
                                       title=KINDS[kind], params=json.dumps(params, ensure_ascii=False), link=link, created=time.time()))
        if config.smtp() or config.notify_webhook():
            job = lambda: self.dispatch(n)  # noqa: E731
            threading.Thread(target=job, daemon=True).start() if self.background else job()
        return n

    def dispatch(self, n: Notification) -> dict:
        """Send to the configured external channels. Never raises. Returns {channel: ok} (for tests/logs)."""
        out = {}
        if (smtp := config.smtp()):
            u = self.users.get_by_id(n.user_id) if self.users else None
            if u: out["email"] = self._email(smtp, u.email, n)
        if (hook := config.notify_webhook()):
            url, secret = hook
            out["webhook"] = webhooks.post(url, {"event": "notification.created", "user_id": n.user_id, **self.public(n)},
                                           [secret] if secret else None, "notification.created").ok
        return out

    @staticmethod
    def _email(smtp: dict, to: str, n: Notification) -> bool:
        p = json.loads(n.params or "{}")
        msg = EmailMessage(); msg["From"] = smtp["sender"]; msg["To"] = to
        msg["Subject"] = f"[LangGraph Studio] {n.title}" + (f": {p['workflow_name']}" if p.get("workflow_name") else "")
        lines = [n.title + "."] + [f"{k}: {p[k]}" for k in ("workflow_name", "label", "prompt") if p.get(k)]
        if n.link: lines.append(f"Open: {config.public_url()}{n.link}")
        msg.set_content("\n".join(lines))
        try:
            cls = smtplib.SMTP_SSL if smtp["ssl"] else smtplib.SMTP
            with cls(smtp["host"], smtp["port"], timeout=10) as s:
                if smtp["starttls"] and not smtp["ssl"]:
                    s.ehlo()
                    if s.has_extn("starttls"): s.starttls(context=ssl.create_default_context()); s.ehlo()
                if smtp["user"]: s.login(smtp["user"], smtp["password"] or "")
                s.send_message(msg)
            return True
        except (OSError, smtplib.SMTPException) as e:
            log.warning("notification e-mail to user %s failed: %s", n.user_id, type(e).__name__); return False

    # ---- owner API ----
    def list(self, uid: str, unread_only: bool = False) -> dict:
        return {"items": [self.public(n) for n in self.repo.list_for_user(uid, unread_only=unread_only)], "unread": self.repo.unread_count(uid)}

    def mark_read(self, uid: str, nid: str) -> dict:
        n = self.repo.get(nid)
        if n is None or n.user_id != uid: raise AppError("NOTIFICATION_NOT_FOUND")
        self.repo.mark_read(uid, nid); return {"ok": True, "unread": self.repo.unread_count(uid)}

    def mark_all_read(self, uid: str) -> dict:
        self.repo.mark_read(uid); return {"ok": True, "unread": 0}
