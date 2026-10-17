from typing import Optional
from sqlalchemy import Boolean, Float, Text, false, true
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    email: Mapped[Optional[str]] = mapped_column(Text, unique=True)
    password: Mapped[Optional[str]] = mapped_column(Text)  # "pbkdf2_sha256$iter$salt$hash"
    created: Mapped[Optional[float]] = mapped_column(Float)
    # notification preferences (TASK-0021)
    notify_in_app: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    notify_email: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    # admins manage org-wide approval channels (TASK-0022 follow-up)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
