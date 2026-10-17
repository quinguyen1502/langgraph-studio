"""Registration, login and token → user resolution."""
import re, time, uuid
from ..core import config, security
from ..core.errors import AppError
from ..repositories import UserRepository
from .workflow_service import WorkflowService

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalise_email(email: str) -> str:
    return email.strip().lower()


class AuthService:
    def __init__(self, users: UserRepository, workflows: WorkflowService):
        self.users, self.workflows = users, workflows

    def _session(self, uid: str, email: str) -> dict:
        return {"token": security.make_token(uid, email), "user": {"id": uid, "email": email}}

    def register(self, email: str, password: str) -> dict:
        email = normalise_email(email)
        if not EMAIL_RE.match(email) or len(email) > 254: raise AppError("AUTH_EMAIL_INVALID")
        if (err := security.password_problem(password)): raise err
        if self.users.get_by_email(email): raise AppError("AUTH_EMAIL_TAKEN")
        uid = uuid.uuid4().hex[:10]
        self.users.add(uid, email, security.hash_password(password), time.time())
        if email in config.admin_emails(): self.users.set_admin(uid)  # STUDIO_ADMIN_EMAILS (org-wide approval channels)
        self.workflows.seed_example(uid)  # new users get a copy of the example workflow
        return self._session(uid, email)

    def login(self, email: str, password: str) -> dict:
        email = normalise_email(email)
        u = self.users.get_by_email(email)
        if not u or not security.verify_password(password, u.password or ""):
            raise AppError("AUTH_INVALID_CREDENTIALS")  # generic: no user enumeration
        return self._session(u.id, email)

    @staticmethod
    def user_from_token(token: str | None) -> dict:
        if not token: raise AppError("AUTH_REQUIRED")
        p = security.decode_token(token)
        return {"id": p["sub"], "email": p["email"]}
