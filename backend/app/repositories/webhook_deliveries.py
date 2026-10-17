from typing import Optional
from sqlalchemy import select, update
from ..models import WebhookDelivery
from ..models.database import Database


class WebhookDeliveryRepository:
    def __init__(self, db: Database): self.db = db

    def add(self, d: WebhookDelivery) -> WebhookDelivery:
        with self.db.session() as s:
            s.add(d); s.commit(); return d

    def add_once(self, d: WebhookDelivery) -> bool:
        """Insert unless a delivery with the same dedupe_key exists (unique column decides under concurrency)."""
        from sqlalchemy.exc import IntegrityError
        with self.db.session() as s:
            try: s.add(d); s.commit(); return True
            except IntegrityError: s.rollback(); return False

    def get(self, did: str) -> Optional[WebhookDelivery]:
        with self.db.session() as s: return s.get(WebhookDelivery, did)

    def update(self, did: str, **fields) -> None:
        with self.db.session() as s:
            s.execute(update(WebhookDelivery).where(WebhookDelivery.id == did).values(**fields)); s.commit()

    def list_for_workflow(self, wid: str, limit: int = 50) -> list[WebhookDelivery]:
        with self.db.session() as s:
            return list(s.scalars(select(WebhookDelivery).where(WebhookDelivery.workflow_id == wid).order_by(WebhookDelivery.created.desc()).limit(limit)))
