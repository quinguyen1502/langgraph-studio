from typing import Optional
from sqlalchemy import Float, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class Run(Base):
    __tablename__ = "runs"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    workflow_id: Mapped[Optional[str]] = mapped_column(Text)
    input: Mapped[Optional[str]] = mapped_column(Text)        # JSON
    events: Mapped[Optional[str]] = mapped_column(Text)       # JSON list
    final_state: Mapped[Optional[str]] = mapped_column(Text)  # JSON
    status: Mapped[Optional[str]] = mapped_column(Text)       # ok | error | cancelled | timeout
    started: Mapped[Optional[float]] = mapped_column(Float)
    ended: Mapped[Optional[float]] = mapped_column(Float)
    # per-run summary metrics (TASK-0010); NULL for runs recorded before 0003
    duration_ms: Mapped[Optional[float]] = mapped_column(Float)
    tokens_in: Mapped[Optional[int]] = mapped_column(Integer)
    tokens_out: Mapped[Optional[int]] = mapped_column(Integer)
    cost_usd: Mapped[Optional[float]] = mapped_column(Float)  # NULL when a model has no known price
    error_count: Mapped[Optional[int]] = mapped_column(Integer)
    trace_id: Mapped[Optional[str]] = mapped_column(Text)     # OTel trace id (hex) when an exporter is configured
    # human-in-the-loop (TASK-0006): owner of the run and the saved checkpoint while status == "waiting"
    owner: Mapped[Optional[str]] = mapped_column(Text, index=True)
    checkpoint: Mapped[Optional[str]] = mapped_column(Text)  # JSON {node, state, workflow}; cleared when the run ends
    source: Mapped[Optional[str]] = mapped_column(Text)  # ui | api (TASK-0007); NULL = ui (older runs)
