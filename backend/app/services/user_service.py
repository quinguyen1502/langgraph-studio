"""User administration (TASK-0014): list accounts, change roles, (de)activate. Callers need users.manage."""
from __future__ import annotations
from ..core import permissions as P
from ..core.errors import AppError
from ..repositories import UserRepository
from .access import AccessService


class UserService:
    def __init__(self, users: UserRepository, access: AccessService):
        self.users, self.access = users, access

    @staticmethod
    def public(u, workflows: int = 0) -> dict:
        return {"id": u.id, "email": u.email, "role": u.role, "active": bool(u.active), "created": u.created, "workflows": workflows}

    def list(self, uid: str) -> dict:
        self.access.require(uid, P.USERS_MANAGE)
        return {"users": [self.public(u, n) for u, n in self.users.list_all()], **P.matrix()}

    def update(self, uid: str, target: str, role: str | None = None, active: bool | None = None) -> dict:
        self.access.require(uid, P.USERS_MANAGE)
        u = self.users.get_by_id(target)
        if u is None: raise AppError("USER_NOT_FOUND")
        if role is not None and role not in P.ROLES: raise AppError("USER_ROLE_INVALID", roles=", ".join(P.ROLES))
        changes_role = role is not None and role != u.role
        deactivates = active is False and u.active
        if target == uid and (changes_role or deactivates): raise AppError("USER_SELF_CHANGE")  # no self-lockout
        if u.role == "admin" and u.active and (changes_role or deactivates) and self.users.count_active_admins() <= 1:
            raise AppError("USER_LAST_ADMIN")
        if changes_role: self.users.set_role(target, role)
        if active is not None and active != bool(u.active): self.users.set_active(target, active)
        return self.public(self.users.get_by_id(target))
