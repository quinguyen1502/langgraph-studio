from typing import Optional
from sqlalchemy import select, update
from ..models import WorkflowToken
from ..models.database import Database


class WorkflowTokenRepository:
    def __init__(self, db: Database): self.db = db

    def add(self, tok: WorkflowToken) -> WorkflowToken:
        with self.db.session() as s:
            s.add(tok); s.commit(); return tok

    def list_for_workflow(self, wid: str) -> list[WorkflowToken]:
        with self.db.session() as s:
            return list(s.scalars(select(WorkflowToken).where(WorkflowToken.workflow_id == wid).order_by(WorkflowToken.created.desc())))

    def get(self, tid: str) -> Optional[WorkflowToken]:
        with self.db.session() as s:
            return s.get(WorkflowToken, tid)

    def by_hash(self, token_hash: str) -> Optional[WorkflowToken]:
        with self.db.session() as s:
            return s.scalars(select(WorkflowToken).where(WorkflowToken.token_hash == token_hash)).first()

    def set_fields(self, tid: str, **values) -> None:
        with self.db.session() as s:
            s.execute(update(WorkflowToken).where(WorkflowToken.id == tid).values(**values)); s.commit()
