import time
from typing import Optional
from sqlalchemy import func, select, update
from ..models import Notification
from ..models.database import Database


class NotificationRepository:
    def __init__(self, db: Database): self.db = db

    def add(self, n: Notification) -> Notification:
        with self.db.session() as s:
            s.add(n); s.commit(); return n

    def list_for_user(self, uid: str, limit: int = 30, unread_only: bool = False) -> list[Notification]:
        with self.db.session() as s:
            q = select(Notification).where(Notification.user_id == uid)
            if unread_only: q = q.where(Notification.read_at.is_(None))
            return list(s.scalars(q.order_by(Notification.created.desc()).limit(limit)))

    def unread_count(self, uid: str) -> int:
        with self.db.session() as s:
            return s.scalar(select(func.count()).select_from(Notification).where(Notification.user_id == uid, Notification.read_at.is_(None))) or 0

    def mark_read(self, uid: str, nid: Optional[str] = None) -> int:
        """Mark one (nid) or all of the user's notifications read. Returns rows changed."""
        with self.db.session() as s:
            q = update(Notification).where(Notification.user_id == uid, Notification.read_at.is_(None))
            if nid: q = q.where(Notification.id == nid)
            n = s.execute(q.values(read_at=time.time())).rowcount; s.commit(); return n or 0

    def get(self, nid: str) -> Optional[Notification]:
        with self.db.session() as s: return s.get(Notification, nid)
