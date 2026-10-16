from typing import Optional
from sqlalchemy import delete, select, update
from ..models import Workflow
from ..models.database import Database


class WorkflowRepository:
    def __init__(self, db: Database): self.db = db

    def list_for_owner(self, owner: str) -> list[Workflow]:
        with self.db.session() as s:
            return list(s.scalars(select(Workflow).where(Workflow.owner == owner).order_by(Workflow.updated.desc())))

    def get(self, wid: str) -> Optional[Workflow]:
        with self.db.session() as s:
            return s.get(Workflow, wid)

    def get_owned(self, wid: str, owner: str) -> Optional[Workflow]:
        w = self.get(wid)
        return w if w is not None and w.owner == owner else None

    def names_for_owner(self, owner: str, exclude: Optional[str] = None) -> set[str]:
        with self.db.session() as s:
            q = select(Workflow.id, Workflow.name).where(Workflow.owner == owner)
            return {name for wid, name in s.execute(q) if wid != exclude}

    def save(self, wid: str, name: str, data: str, updated: float, owner: str) -> None:
        """Insert or replace (same semantics as the MVP's INSERT OR REPLACE)."""
        with self.db.session() as s:
            s.merge(Workflow(id=wid, name=name, data=data, updated=updated, owner=owner)); s.commit()

    def update_name(self, wid: str, name: str, data: str, updated: float) -> None:
        with self.db.session() as s:
            s.execute(update(Workflow).where(Workflow.id == wid).values(name=name, data=data, updated=updated)); s.commit()

    def delete(self, wid: str) -> None:
        with self.db.session() as s:
            s.execute(delete(Workflow).where(Workflow.id == wid)); s.commit()

    def exists(self, wid: str) -> bool:
        return self.get(wid) is not None

    def adopt_unowned(self, owner: str) -> None:
        with self.db.session() as s:
            s.execute(update(Workflow).where(Workflow.owner.is_(None)).values(owner=owner)); s.commit()
