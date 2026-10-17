import json
from typing import Any, Optional
from sqlalchemy import func, or_, select
from ..models import AuditEvent, StudioSetting
from ..models.database import Database


class AuditRepository:
    def __init__(self, db: Database): self.db = db

    def add(self, e: AuditEvent) -> None:
        with self.db.session() as s: s.add(e); s.commit()

    def query(self, *, category: Optional[str] = None, q: Optional[str] = None, since: Optional[float] = None,
              limit: int = 50, offset: int = 0) -> tuple[list[AuditEvent], int]:
        """Newest first. category: action prefix (`user`, `share`, `team`, `workflow`, `policy`); q: actor, target or action text."""
        conds = []
        if category: conds.append(AuditEvent.action.like(f"{category}.%"))
        if since: conds.append(AuditEvent.ts >= since)
        if q:
            like = f"%{q.lower()}%"
            conds.append(or_(func.lower(AuditEvent.actor_email).like(like), func.lower(AuditEvent.target_label).like(like),
                             func.lower(AuditEvent.action).like(like), AuditEvent.target_id == q))
        with self.db.session() as s:
            total = s.scalar(select(func.count(AuditEvent.id)).where(*conds)) or 0
            rows = list(s.scalars(select(AuditEvent).where(*conds).order_by(AuditEvent.ts.desc()).limit(limit).offset(offset)))
        return rows, int(total)


class SettingsRepository:
    def __init__(self, db: Database): self.db = db

    def get(self, key: str, default: Any = None) -> Any:
        with self.db.session() as s:
            row = s.get(StudioSetting, key)
            return json.loads(row.value) if row else default

    def set(self, key: str, value: Any, uid: Optional[str], now: float) -> None:
        with self.db.session() as s:
            s.merge(StudioSetting(key=key, value=json.dumps(value), updated=now, updated_by=uid)); s.commit()
