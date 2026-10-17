from typing import Optional
from sqlalchemy import select
from ..models import User
from ..models.database import Database


class UserRepository:
    def __init__(self, db: Database): self.db = db

    def get_by_email(self, email: str) -> Optional[User]:
        with self.db.session() as s:
            return s.scalars(select(User).where(User.email == email)).first()

    def get_by_id(self, uid: str) -> Optional[User]:
        with self.db.session() as s:
            return s.get(User, uid)

    def add(self, uid: str, email: str, password_hash: str, created: float) -> User:
        with self.db.session() as s:
            u = User(id=uid, email=email, password=password_hash, created=created); s.add(u); s.commit(); return u

    def set_prefs(self, uid: str, **prefs: bool) -> Optional[User]:
        """Notification preferences (TASK-0021): notify_in_app / notify_email."""
        with self.db.session() as s:
            u = s.get(User, uid)
            if u is None: return None
            for k, v in prefs.items(): setattr(u, k, bool(v))
            s.commit(); s.refresh(u); return u
