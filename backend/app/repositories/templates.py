from typing import Optional
from sqlalchemy import delete, or_, select
from ..models import WorkflowTemplate
from ..models.database import Database


class TemplateRepository:
    def __init__(self, db: Database): self.db = db

    def visible(self, uid: str) -> list[WorkflowTemplate]:
        """The caller's personal templates and every org-wide one, by name."""
        with self.db.session() as s:
            return list(s.scalars(select(WorkflowTemplate).where(or_(WorkflowTemplate.owner == uid, WorkflowTemplate.scope == "org"))
                                  .order_by(WorkflowTemplate.name)))

    def get(self, tid: str) -> Optional[WorkflowTemplate]:
        with self.db.session() as s: return s.get(WorkflowTemplate, tid)

    def add(self, t: WorkflowTemplate) -> None:
        with self.db.session() as s: s.add(t); s.commit()

    def delete(self, tid: str) -> None:
        with self.db.session() as s: s.execute(delete(WorkflowTemplate).where(WorkflowTemplate.id == tid)); s.commit()
