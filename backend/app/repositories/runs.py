from typing import Optional
from sqlalchemy import delete, select, update
from ..models import Run
from ..models.database import Database


class RunRepository:
    def __init__(self, db: Database): self.db = db

    def add(self, run: Run) -> None:
        """Insert or update (a resumed run keeps its id)."""
        with self.db.session() as s:
            s.merge(run); s.commit()

    def get(self, rid: str) -> Optional[Run]:
        with self.db.session() as s:
            return s.get(Run, rid)

    def set_status(self, rid: str, status: str) -> None:
        with self.db.session() as s:
            s.execute(update(Run).where(Run.id == rid).values(status=status)); s.commit()

    def save_progress(self, rid: str, events: str, checkpoint: str) -> None:
        """Progress checkpoint of a running queue job (TASK-0020); only while it is still running."""
        with self.db.session() as s:
            s.execute(update(Run).where(Run.id == rid, Run.status == "running").values(events=events, checkpoint=checkpoint)); s.commit()

    def list_waiting(self, owner: str, limit: int = 100) -> list[Run]:
        with self.db.session() as s:
            return list(s.scalars(select(Run).where(Run.owner == owner, Run.status == "waiting").order_by(Run.started.desc()).limit(limit)))

    def list_waiting_before(self, cutoff: float, limit: int = 500) -> list[Run]:
        """Waiting runs (any owner) paused before `cutoff` (Run.ended = time it started waiting)."""
        with self.db.session() as s:
            return list(s.scalars(select(Run).where(Run.status == "waiting", Run.ended < cutoff).limit(limit)))

    def last_for_workflow(self, wid: str) -> Optional[Run]:
        with self.db.session() as s:
            return s.scalars(select(Run).where(Run.workflow_id == wid).order_by(Run.started.desc()).limit(1)).first()

    def list_for_workflow(self, wid: str, limit: int = 50) -> list[Run]:
        with self.db.session() as s:
            return list(s.scalars(select(Run).where(Run.workflow_id == wid).order_by(Run.started.desc()).limit(limit)))

    def delete_for_workflow(self, wid: str) -> None:
        with self.db.session() as s:
            s.execute(delete(Run).where(Run.workflow_id == wid)); s.commit()
