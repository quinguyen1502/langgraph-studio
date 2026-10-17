from typing import Optional
from sqlalchemy import Float, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class WebhookDelivery(Base):
    """One result-webhook delivery and its attempts (TASK-0020)."""
    __tablename__ = "webhook_deliveries"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    workflow_id: Mapped[str] = mapped_column(Text, index=True)
    run_id: Mapped[Optional[str]] = mapped_column(Text)
    token_id: Mapped[Optional[str]] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text)
    event: Mapped[str] = mapped_column(Text)               # run.finished
    payload: Mapped[str] = mapped_column(Text)             # JSON body (re-sent on redelivery)
    status: Mapped[str] = mapped_column(Text)              # pending | retrying | ok | failed
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    response_code: Mapped[Optional[int]] = mapped_column(Integer)
    latency_ms: Mapped[Optional[float]] = mapped_column(Float)
    last_error: Mapped[Optional[str]] = mapped_column(Text)
    next_attempt: Mapped[Optional[float]] = mapped_column(Float)
    created: Mapped[float] = mapped_column(Float)
    updated: Mapped[Optional[float]] = mapped_column(Float)
