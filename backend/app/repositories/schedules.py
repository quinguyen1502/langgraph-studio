from typing import Optional
from sqlalchemy import delete, select, update
from ..models import WorkflowSchedule
from ..models.database import Database


class ScheduleRepository:
    def __init__(self, db: Database): self.db = db

    def add(self, s_: WorkflowSchedule) -> WorkflowSchedule:
        with self.db.session() as s: s.add(s_); s.commit(); s.refresh(s_); return s_

    def get(self, sid: str) -> Optional[WorkflowSchedule]:
        with self.db.session() as s: return s.get(WorkflowSchedule, sid)

    def list_for_workflow(self, wid: str) -> list[WorkflowSchedule]:
        with self.db.session() as s:
            return list(s.scalars(select(WorkflowSchedule).where(WorkflowSchedule.workflow_id == wid).order_by(WorkflowSchedule.created)))

    def count_for_workflow(self, wid: str) -> int:
        return len(self.list_for_workflow(wid))

    def set_fields(self, sid: str, **values) -> None:
        with self.db.session() as s: s.execute(update(WorkflowSchedule).where(WorkflowSchedule.id == sid).values(**values)); s.commit()

    def delete(self, sid: str) -> None:
        with self.db.session() as s: s.execute(delete(WorkflowSchedule).where(WorkflowSchedule.id == sid)); s.commit()

    def due(self, now: float, limit: int = 50) -> list[WorkflowSchedule]:
        with self.db.session() as s:
            return list(s.scalars(select(WorkflowSchedule).where(WorkflowSchedule.enabled.is_(True), WorkflowSchedule.next_run <= now)
                                  .order_by(WorkflowSchedule.next_run).limit(limit)))

    def claim(self, sid: str, seen_next: float, new_next: Optional[float], now: float) -> bool:
        """Move next_run on only if nobody else did (several workers may see the same due row): True means fire it."""
        with self.db.session() as s:
            n = s.execute(update(WorkflowSchedule).where(WorkflowSchedule.id == sid, WorkflowSchedule.next_run == seen_next)
                          .values(next_run=new_next, last_run=now)).rowcount
            s.commit(); return bool(n)
