from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from ..models import ChatMessage
from ..models.database import Database


class ChatMessageRepository:
    def __init__(self, db: Database): self.db = db

    def add_once(self, m: ChatMessage) -> bool:
        """Insert unless this connection already has a message with the same key (unique index decides under concurrency)."""
        with self.db.session() as s:
            try: s.add(m); s.commit(); return True
            except IntegrityError: s.rollback(); return False

    def get(self, mid: str) -> Optional[ChatMessage]:
        with self.db.session() as s: return s.get(ChatMessage, mid)

    def by_run(self, rid: str) -> Optional[ChatMessage]:
        with self.db.session() as s: return s.scalar(select(ChatMessage).where(ChatMessage.run_id == rid))

    def by_runs(self, rids: list[str]) -> list[ChatMessage]:
        if not rids: return []
        with self.db.session() as s: return list(s.scalars(select(ChatMessage).where(ChatMessage.run_id.in_(rids))))

    def set_fields(self, mid: str, **values) -> None:
        with self.db.session() as s: s.execute(update(ChatMessage).where(ChatMessage.id == mid).values(**values)); s.commit()

    def claim(self, mid: str) -> bool:
        """queued -> checking, once: a job a dead worker left behind and its recovered copy start one run."""
        with self.db.session() as s:
            n = s.execute(update(ChatMessage).where(ChatMessage.id == mid, ChatMessage.status == "queued").values(status="checking")).rowcount
            s.commit(); return bool(n)

    def mark_replied(self, mid: str, seen: Optional[str], new: str) -> bool:
        """Compare-and-set the last reply, so a settled state is replied once however often settled() runs."""
        with self.db.session() as s:
            cond = ChatMessage.replied.is_(None) if seen is None else ChatMessage.replied == seen
            n = s.execute(update(ChatMessage).where(ChatMessage.id == mid, cond).values(replied=new)).rowcount; s.commit(); return bool(n)
