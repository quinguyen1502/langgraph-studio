from typing import Optional
from sqlalchemy import delete, func, select
from ..models import Run, User, WorkflowVersion
from ..models.database import Database


class WorkflowVersionRepository:
    def __init__(self, db: Database): self.db = db

    def latest(self, wid: str) -> Optional[WorkflowVersion]:
        with self.db.session() as s:
            return s.scalars(select(WorkflowVersion).where(WorkflowVersion.workflow_id == wid).order_by(WorkflowVersion.version.desc()).limit(1)).first()

    def get(self, wid: str, version: int) -> Optional[WorkflowVersion]:
        with self.db.session() as s:
            return s.scalars(select(WorkflowVersion).where(WorkflowVersion.workflow_id == wid, WorkflowVersion.version == version)).first()

    def list_with_authors(self, wid: str, limit: int = 50, offset: int = 0) -> list[tuple[WorkflowVersion, Optional[str]]]:
        """Newest first, with the author's email (users may have been deleted: None)."""
        with self.db.session() as s:
            q = (select(WorkflowVersion, User.email).outerjoin(User, User.id == WorkflowVersion.author)
                 .where(WorkflowVersion.workflow_id == wid).order_by(WorkflowVersion.version.desc()).limit(limit).offset(offset))
            return [(v, e) for v, e in s.execute(q)]

    def count(self, wid: str) -> int:
        with self.db.session() as s:
            return s.scalar(select(func.count()).select_from(WorkflowVersion).where(WorkflowVersion.workflow_id == wid)) or 0

    def prune(self, wid: str, keep: int) -> int:
        """Delete all but the newest `keep` versions, except versions referenced by runs. Returns the count deleted."""
        with self.db.session() as s:
            newest = select(WorkflowVersion.version).where(WorkflowVersion.workflow_id == wid).order_by(WorkflowVersion.version.desc()).limit(keep)
            used = select(Run.workflow_version).where(Run.workflow_id == wid, Run.workflow_version.is_not(None))
            res = s.execute(delete(WorkflowVersion).where(WorkflowVersion.workflow_id == wid,
                                                          WorkflowVersion.version.not_in(newest.scalar_subquery()),
                                                          WorkflowVersion.version.not_in(used.scalar_subquery())))
            s.commit(); return res.rowcount or 0

    def next_number(self, wid: str) -> int:
        with self.db.session() as s:
            return (s.scalar(select(func.max(WorkflowVersion.version)).where(WorkflowVersion.workflow_id == wid)) or 0) + 1

    def add(self, v: WorkflowVersion) -> WorkflowVersion:
        with self.db.session() as s:
            s.add(v); s.commit(); return v

    def delete_for_workflow(self, wid: str) -> None:
        with self.db.session() as s:
            s.execute(delete(WorkflowVersion).where(WorkflowVersion.workflow_id == wid)); s.commit()
