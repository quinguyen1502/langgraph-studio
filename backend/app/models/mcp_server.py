"""Registered MCP servers (TASK-0013). Secrets (stdio env vars / HTTP headers) are one Fernet token, never returned."""
from typing import Optional
from sqlalchemy import Float, Text
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class McpServer(Base):
    __tablename__ = "mcp_servers"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    owner: Mapped[str] = mapped_column(Text, index=True)
    scope: Mapped[str] = mapped_column(Text, default="user")     # user (owner only) | org (admin-managed, usable by everyone)
    name: Mapped[str] = mapped_column(Text)
    transport: Mapped[str] = mapped_column(Text)                 # stdio | http
    command: Mapped[Optional[str]] = mapped_column(Text)         # stdio
    args: Mapped[Optional[str]] = mapped_column(Text)            # stdio: JSON list of strings
    url: Mapped[Optional[str]] = mapped_column(Text)             # http (Streamable HTTP endpoint)
    secrets: Mapped[Optional[str]] = mapped_column(Text)         # Fernet(JSON {name: value}): env vars (stdio) or headers (http)
    secret_hints: Mapped[Optional[str]] = mapped_column(Text)    # JSON {name: masked value}
    tools: Mapped[Optional[str]] = mapped_column(Text)           # JSON list from the last discovery
    tools_at: Mapped[Optional[float]] = mapped_column(Float)
    created: Mapped[float] = mapped_column(Float)
