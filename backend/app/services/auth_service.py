"""Registration, login and token → user resolution."""
import re, time, uuid
from ..core import security
from ..core.errors import BadRequest, Conflict, Unauthorized
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
        if not EMAIL_RE.match(email) or len(email) > 254: raise BadRequest("Email không hợp lệ")
        if (msg := security.password_problem(password)): raise BadRequest(msg)
        if self.users.get_by_email(email): raise Conflict("Email đã được đăng ký")
        uid = uuid.uuid4().hex[:10]
        self.users.add(uid, email, security.hash_password(password), time.time())
        self.workflows.seed_example(uid)  # new users get a copy of the example workflow
        return self._session(uid, email)

    def login(self, email: str, password: str) -> dict:
        email = normalise_email(email)
        u = self.users.get_by_email(email)
        if not u or not security.verify_password(password, u.password or ""):
            raise Unauthorized("Sai email hoặc mật khẩu")  # generic: no user enumeration
        return self._session(u.id, email)

    @staticmethod
    def user_from_token(token: str | None) -> dict:
        if not token: raise Unauthorized("Chưa đăng nhập")
        p = security.decode_token(token)
        return {"id": p["sub"], "email": p["email"]}
