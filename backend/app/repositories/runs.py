from typing import Optional
from sqlalchemy import delete, select
from ..models import Run
from ..models.database import Database


class RunRepository:
    def __init__(self, db: Database): self.db = db

    def add(self, run: Run) -> None:
        with self.db.session() as s:
            s.add(run); s.commit()

    def last_for_workflow(self, wid: str) -> Optional[Run]:
        with self.db.session() as s:
            return s.scalars(select(Run).where(Run.workflow_id == wid).order_by(Run.started.desc()).limit(1)).first()

    def list_for_workflow(self, wid: str, limit: int = 50) -> list[Run]:
        with self.db.session() as s:
            return list(s.scalars(select(Run).where(Run.workflow_id == wid).order_by(Run.started.desc()).limit(limit)))

    def delete_for_workflow(self, wid: str) -> None:
        with self.db.session() as s:
            s.execute(delete(Run).where(Run.workflow_id == wid)); s.commit()
