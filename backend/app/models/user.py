from typing import Optional
from sqlalchemy import Float, Text
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    email: Mapped[Optional[str]] = mapped_column(Text, unique=True)
    password: Mapped[Optional[str]] = mapped_column(Text)  # "pbkdf2_sha256$iter$salt$hash"
    created: Mapped[Optional[float]] = mapped_column(Float)
