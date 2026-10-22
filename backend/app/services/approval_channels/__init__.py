"""Approval channel adapters (TASK-0022). Buttons: Slack, Telegram, WhatsApp. Links to the studio: e-mail, Teams (TASK-0047)."""
from .base import ApprovalChannel, ApprovalMessage, Callback, IncomingMessage
from .links import EmailChannel, TeamsChannel
from .slack import SlackChannel
from .telegram import TelegramChannel
from .whatsapp import WhatsAppChannel

ADAPTERS: dict[str, ApprovalChannel] = {a.kind: a for a in (SlackChannel(), TelegramChannel(), WhatsAppChannel(), EmailChannel(), TeamsChannel())}

__all__ = ["ADAPTERS", "ApprovalChannel", "ApprovalMessage", "Callback", "IncomingMessage"]
