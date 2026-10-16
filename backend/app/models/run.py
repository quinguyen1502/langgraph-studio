from typing import Optional
from sqlalchemy import Float, Text
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
