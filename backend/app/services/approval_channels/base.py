"""ApprovalChannel adapter interface (TASK-0022, DEC-0019).

An adapter knows one messaging platform: how to post an approval request with two buttons, how to authenticate and
parse the platform's callback, and how to edit the original message afterwards. Business rules (tokens, identity
mapping, authorization, audit, resuming the run) live in ApprovalService, so a new channel (WhatsApp, Teams, e-mail)
is one more subclass registered in `ADAPTERS`.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Any, Optional
import httpx
from ...core.errors import AppError


@dataclass
class ApprovalMessage:
    """What an approval request says, channel-neutral (plain text; adapters format it)."""
    title: str
    lines: list[str]
    link: Optional[str]
    approve_token: str
    reject_token: str


@dataclass
class Callback:
    """A button press, parsed from the platform's callback."""
    token: str
    external_user: str
    context: dict = field(default_factory=dict)  # what acknowledge() needs (response_url, callback_query_id, ...)


class ApprovalChannel:
    kind: str = ""
    label: str = ""                         # display name in messages ("Slack")
    fields: tuple[str, ...] = ()            # secret settings the owner enters (all encrypted)
    optional: tuple[str, ...] = ()          # of those, the ones that may be empty (adapter fills a default)
    patterns: dict[str, str] = {}           # field -> regex it must match
    identity_pattern: str = r".+"           # shape of a platform user id
    hint_field: str = ""                    # which secret the masked hint shows
    transport: Optional[httpx.BaseTransport] = None  # tests plug in httpx.MockTransport

    # ---- configuration ----
    def prepare(self, values: dict) -> dict:
        """Validate the owner's settings; returns the dict to encrypt. Raises CHANNEL_CONFIG_INVALID {field}."""
        out = {}
        for f in self.fields:
            v = values.get(f); v = v.strip() if isinstance(v, str) else v
            if not v:
                if f in self.optional: continue
                raise AppError("CHANNEL_CONFIG_INVALID", field=f)
            if not isinstance(v, str) or (f in self.patterns and not re.fullmatch(self.patterns[f], v)): raise AppError("CHANNEL_CONFIG_INVALID", field=f)
            out[f] = v
        return out

    def valid_identity(self, external_id: str) -> bool: return bool(re.fullmatch(self.identity_pattern, external_id))

    def register(self, secrets: dict, callback_url: str) -> dict:
        """Point the platform at our callback URL when its API allows it. Default: manual setup, nothing to do."""
        return {"registered": False, "manual": True}

    # ---- the four operations ----
    def send_request(self, secrets: dict, target: str, msg: ApprovalMessage) -> dict:
        """Post the request with Approve/Reject buttons. Returns the message reference used by update()."""
        raise NotImplementedError

    def verify(self, secrets: dict, headers: dict, body: bytes) -> None:
        """Authenticate a callback (signature / secret header). Raises CHANNEL_SIGNATURE_INVALID."""
        raise NotImplementedError

    def handle_callback(self, body: bytes) -> Optional[Callback]:
        """Parse a verified callback into a button press; None for events that are not one (ignored)."""
        raise NotImplementedError

    def acknowledge(self, secrets: dict, cb: Callback, text: str, accepted: bool) -> None:
        """Tell the person who pressed the button what happened (only them when refused)."""

    def update(self, secrets: dict, ref: dict, text: str) -> None:
        """Replace the original message (buttons removed) with the outcome."""
        raise NotImplementedError

    # ---- HTTP helper ----
    def call(self, method: str, url: str, **kw) -> Any:
        try:
            with httpx.Client(timeout=10, transport=self.transport) as c: r = c.request(method, url, **kw)
            data = r.json()
        except (httpx.HTTPError, ValueError) as e: raise AppError("CHANNEL_API_FAILED", kind=self.label, reason=type(e).__name__)
        return r, data
