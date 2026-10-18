from typing import Optional
from sqlalchemy import delete, select
from ..models import Credential
from ..models.database import Database


class CredentialRepository:
    def __init__(self, db: Database): self.db = db

    def add(self, cred: Credential) -> Credential:
        with self.db.session() as s:
            s.add(cred); s.commit(); return cred

    def list_for_owner(self, owner: str) -> list[Credential]:
        with self.db.session() as s:
            return list(s.scalars(select(Credential).where(Credential.owner == owner).order_by(Credential.created.desc())))

    def get_owned(self, cid: str, owner: str) -> Optional[Credential]:
        with self.db.session() as s:
            return s.scalars(select(Credential).where(Credential.id == cid, Credential.owner == owner)).first()

    def update_owned(self, cid: str, owner: str, **values) -> Optional[Credential]:
        with self.db.session() as s:
            c = s.scalars(select(Credential).where(Credential.id == cid, Credential.owner == owner)).first()
            if c is None: return None
            for k, v in values.items(): setattr(c, k, v)
            s.commit(); s.refresh(c); return c

    def delete_owned(self, cid: str, owner: str) -> bool:
        with self.db.session() as s:
            n = s.execute(delete(Credential).where(Credential.id == cid, Credential.owner == owner)).rowcount; s.commit()
            return bool(n)
