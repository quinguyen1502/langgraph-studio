from typing import Optional
from sqlalchemy import select
from ..models import User
from ..models.database import Database


class UserRepository:
    def __init__(self, db: Database): self.db = db

    def get_by_email(self, email: str) -> Optional[User]:
        with self.db.session() as s:
            return s.scalars(select(User).where(User.email == email)).first()

    def add(self, uid: str, email: str, password_hash: str, created: float) -> User:
        with self.db.session() as s:
            u = User(id=uid, email=email, password=password_hash, created=created); s.add(u); s.commit(); return u
