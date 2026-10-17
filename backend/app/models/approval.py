"""Human-in-the-loop approval through external channels (TASK-0022, DEC-0019)."""
from typing import Optional
from sqlalchemy import Float, Index, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class ApprovalChannel(Base):
    """A connected channel (Slack app / Telegram bot); secrets are one Fernet-encrypted JSON.
    scope "user": usable by its owner only. scope "org": created by an admin (owner), usable by every user."""
    __tablename__ = "approval_channels"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    owner: Mapped[str] = mapped_column(Text, index=True)
    kind: Mapped[str] = mapped_column(Text)              # slack | telegram (registry in services/approval_channels)
    scope: Mapped[str] = mapped_column(Text, default="user", server_default="user", index=True)  # user | org
    name: Mapped[Optional[str]] = mapped_column(Text)    # display name (workspace / bot)
    secrets: Mapped[str] = mapped_column(Text)           # Fernet token of {field: value}; never returned by the API
    hint: Mapped[Optional[str]] = mapped_column(Text)    # masked last 4 chars of the main token
    created: Mapped[float] = mapped_column(Float)


class ChannelIdentity(Base):
    """Maps a channel account (Slack user id, Telegram user id) to a studio user. Only a *verified* link (the user typed
    the one-time code the bot sent to that account) authorizes button presses; one verified link per account."""
    __tablename__ = "channel_identities"
    __table_args__ = (Index("ix_channel_identities_external", "kind", "external_id"),)
    user_id: Mapped[str] = mapped_column(Text, primary_key=True)
    kind: Mapped[str] = mapped_column(Text, primary_key=True)
    external_id: Mapped[str] = mapped_column(Text)
    created: Mapped[float] = mapped_column(Float)
    verified_at: Mapped[Optional[float]] = mapped_column(Float)
    code_hash: Mapped[Optional[str]] = mapped_column(Text)       # HMAC of the pending one-time code (never the code)
    code_expires: Mapped[Optional[float]] = mapped_column(Float)
    code_sent_at: Mapped[Optional[float]] = mapped_column(Float)  # resend throttle
    code_attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0")  # wrong codes for the pending one


class ApprovalRequest(Base):
    """One approval message sent for a waiting run. Tokens are signed with `nonce` + `expires`; single use = CAS on status."""
    __tablename__ = "approval_requests"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    run_id: Mapped[str] = mapped_column(Text, index=True)
    node_id: Mapped[str] = mapped_column(Text)
    owner: Mapped[str] = mapped_column(Text, index=True)
    workflow_id: Mapped[Optional[str]] = mapped_column(Text)
    channel_id: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(Text)
    target: Mapped[str] = mapped_column(Text)             # Slack channel id / Telegram chat id
    approvers: Mapped[str] = mapped_column(Text)          # JSON list of studio user ids allowed besides the owner
    nonce: Mapped[str] = mapped_column(Text)
    expires: Mapped[float] = mapped_column(Float)
    message_ref: Mapped[Optional[str]] = mapped_column(Text)  # JSON, e.g. {channel, ts} / {chat_id, message_id}
    status: Mapped[str] = mapped_column(Text)             # pending | approved | rejected | expired | superseded | failed
    decided_by: Mapped[Optional[str]] = mapped_column(Text)   # studio user id
    decided_external: Mapped[Optional[str]] = mapped_column(Text)
    decided_at: Mapped[Optional[float]] = mapped_column(Float)
    created: Mapped[float] = mapped_column(Float)


class ApprovalAudit(Base):
    """Append-only log of every approval request, decision and refused attempt."""
    __tablename__ = "approval_audit"
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    owner: Mapped[str] = mapped_column(Text, index=True)  # run owner (who may read the entry)
    request_id: Mapped[Optional[str]] = mapped_column(Text)
    run_id: Mapped[Optional[str]] = mapped_column(Text)
    workflow_id: Mapped[Optional[str]] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(Text)
    action: Mapped[str] = mapped_column(Text)  # requested | approved | rejected | denied | superseded | expired | send_failed | not_configured
    code: Mapped[Optional[str]] = mapped_column(Text)  # error code of a refused attempt / failure
    actor_id: Mapped[Optional[str]] = mapped_column(Text)     # studio user id (when mapped)
    external_id: Mapped[Optional[str]] = mapped_column(Text)  # channel user id
    created: Mapped[float] = mapped_column(Float, index=True)
