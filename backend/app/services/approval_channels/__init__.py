"""Approval channel adapters (TASK-0022). Add WhatsApp / Teams / e-mail by subclassing ApprovalChannel and registering it here."""
from .base import ApprovalChannel, ApprovalMessage, Callback
from .slack import SlackChannel
from .telegram import TelegramChannel

ADAPTERS: dict[str, ApprovalChannel] = {a.kind: a for a in (SlackChannel(), TelegramChannel())}

__all__ = ["ADAPTERS", "ApprovalChannel", "ApprovalMessage", "Callback"]
