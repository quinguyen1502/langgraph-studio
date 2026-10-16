from typing import Optional
from sqlalchemy import Float, Text
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class Workflow(Base):
    __tablename__ = "workflows"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(Text)
    data: Mapped[Optional[str]] = mapped_column(Text)  # workflow JSON (nodes, edges, state, source?)
    updated: Mapped[Optional[float]] = mapped_column(Float)
    owner: Mapped[Optional[str]] = mapped_column(Text)
