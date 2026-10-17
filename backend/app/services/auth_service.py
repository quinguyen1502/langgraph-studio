"""Registration, login and token → user resolution (with the user's role, TASK-0014)."""
import re, time, uuid
from ..core import config, security
from ..core import permissions as P
from ..core.errors import AppError
from ..repositories import UserRepository

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalise_email(email: str) -> str:
    return email.strip().lower()


def public_user(u) -> dict:
    return {"id": u.id, "email": u.email, "role": u.role, "permissions": sorted(P.PERMISSIONS.get(u.role, ())),
            "is_admin": u.role == "admin"}


class AuthService:
    def __init__(self, users: UserRepository, workflows=None):
        self.users, self.workflows = users, workflows  # workflows: WorkflowService (seeds the example for new users)

    def _session(self, uid: str) -> dict:
        u = self.users.get_by_id(uid)
        return {"token": security.make_token(uid, u.email), "user": public_user(u)}

    def register(self, email: str, password: str) -> dict:
        email = normalise_email(email)
        if not EMAIL_RE.match(email) or len(email) > 254: raise AppError("AUTH_EMAIL_INVALID")
        if (err := security.password_problem(password)): raise err
        if self.users.get_by_email(email): raise AppError("AUTH_EMAIL_TAKEN")
        uid = uuid.uuid4().hex[:10]
        self.users.add(uid, email, security.hash_password(password), time.time())
        # STUDIO_ADMIN_EMAILS bootstraps admins at sign-up; everyone else gets STUDIO_DEFAULT_ROLE (editor)
        self.users.set_role(uid, "admin" if email in config.admin_emails() else config.default_role())
        if self.workflows is not None and P.can(self.users.get_by_id(uid).role, P.WORKFLOWS_CREATE):
            self.workflows.seed_example(uid)  # new users get a copy of the example workflow
        return self._session(uid)

    def login(self, email: str, password: str) -> dict:
        email = normalise_email(email)
        u = self.users.get_by_email(email)
        if not u or not security.verify_password(password, u.password or ""):
            raise AppError("AUTH_INVALID_CREDENTIALS")  # generic: no user enumeration
        if not u.active: raise AppError("AUTH_ACCOUNT_DISABLED")
        return self._session(u.id)

    @staticmethod
    def user_from_token(token: str | None) -> dict:
        """Signature check only (no database): {id, email}. Use `current` for requests."""
        if not token: raise AppError("AUTH_REQUIRED")
        p = security.decode_token(token)
        return {"id": p["sub"], "email": p["email"]}

    def current(self, token: str | None) -> dict:
        """The signed-in user, checked against the database: deleted or deactivated accounts lose access at once."""
        uid = self.user_from_token(token)["id"]
        u = self.users.get_by_id(uid)
        if u is None: raise AppError("AUTH_TOKEN_INVALID")
        if not u.active: raise AppError("AUTH_ACCOUNT_DISABLED")
        return public_user(u)
