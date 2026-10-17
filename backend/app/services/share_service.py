"""Workflow sharing (TASK-0014): the owner (or an admin) shares a workflow with a user as viewer or editor."""
from __future__ import annotations
import time
from ..core import permissions as P
from ..core.errors import AppError
from ..models import WorkflowShare
from ..repositories import UserRepository, WorkflowShareRepository
from .access import AccessService
from .auth_service import normalise_email


class ShareService:
    def __init__(self, shares: WorkflowShareRepository, users: UserRepository, access: AccessService):
        self.shares, self.users, self.access = shares, users, access

    def list(self, wid: str, uid: str) -> dict:
        w = self.access.workflow(wid, uid, P.VIEW)
        owner = self.users.get_by_id(w.owner)
        return {"owner": {"id": w.owner, "email": owner.email if owner else None},
                "can_share": self.access.may(wid, uid, P.SHARE),
                "shares": [{"user_id": s.user_id, "email": e, "role": s.role, "created": s.created} for s, e in self.shares.for_workflow(wid)]}

    def put(self, wid: str, uid: str, email: str, role: str) -> dict:
        """Share with (or change the role of) the account with this email."""
        w = self.access.workflow(wid, uid, P.SHARE)
        if role not in P.SHARE_ROLES: raise AppError("SHARE_ROLE_INVALID")
        u = self.users.get_by_email(normalise_email(email or ""))
        if u is None or not u.active: raise AppError("SHARE_USER_NOT_FOUND")
        if u.id == w.owner: raise AppError("SHARE_OWNER")
        self.shares.upsert(WorkflowShare(workflow_id=wid, user_id=u.id, role=role, created=time.time(), shared_by=uid))
        return self.list(wid, uid)

    def remove(self, wid: str, uid: str, target: str) -> dict:
        """The owner or an admin removes anyone; a user may also leave a workflow shared with them."""
        if target != uid: self.access.workflow(wid, uid, P.SHARE)
        if not self.shares.remove(wid, target): raise AppError("SHARE_NOT_FOUND")
        return {"ok": True}
