from typing import Optional
from sqlalchemy import delete, select
from ..models import User, WorkflowShare
from ..models.database import Database


class WorkflowShareRepository:
    def __init__(self, db: Database): self.db = db

    def role_of(self, wid: str, uid: str) -> Optional[str]:
        with self.db.session() as s:
            return s.scalar(select(WorkflowShare.role).where(WorkflowShare.workflow_id == wid, WorkflowShare.user_id == uid))

    def for_workflow(self, wid: str) -> list[tuple[WorkflowShare, str]]:
        """(share, user email), in the order they were shared."""
        with self.db.session() as s:
            return [(sh, e) for sh, e in s.execute(select(WorkflowShare, User.email).join(User, User.id == WorkflowShare.user_id)
                                                   .where(WorkflowShare.workflow_id == wid).order_by(WorkflowShare.created))]

    def for_user(self, uid: str) -> dict[str, str]:
        """workflow id -> role of the workflows shared with this user."""
        with self.db.session() as s:
            return {w: r for w, r in s.execute(select(WorkflowShare.workflow_id, WorkflowShare.role).where(WorkflowShare.user_id == uid))}

    def upsert(self, row: WorkflowShare) -> None:
        with self.db.session() as s: s.merge(row); s.commit()

    def remove(self, wid: str, uid: str) -> bool:
        with self.db.session() as s:
            n = s.execute(delete(WorkflowShare).where(WorkflowShare.workflow_id == wid, WorkflowShare.user_id == uid)).rowcount; s.commit()
            return bool(n)

    def delete_for_workflow(self, wid: str) -> None:
        with self.db.session() as s: s.execute(delete(WorkflowShare).where(WorkflowShare.workflow_id == wid)); s.commit()
