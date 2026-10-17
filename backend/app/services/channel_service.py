"""Approval channel connections (TASK-0022, DEC-0019): personal ones and org-wide ones managed by admins.

scope "user": the owner's own Slack app / Telegram bot, usable on the owner's Human nodes only.
scope "org":  created by an admin (users.is_admin), usable by every user; only admins edit or delete it.
Secrets are Fernet-encrypted and never returned; the API shows a masked hint.
"""
import json, time
from typing import Optional
from ..core import config, crypto
from ..core.errors import AppError
from ..models import ApprovalChannel as ChannelRow
from ..repositories import ApprovalRepository, UserRepository
from .approval_channels import ApprovalChannel

SCOPES = ("user", "org")


def callback_path(kind: str, cid: str) -> str: return f"/api/approvals/callback/{kind}/{cid}"


class ChannelService:
    def __init__(self, repo: ApprovalRepository, users: UserRepository, adapters: dict[str, ApprovalChannel]):
        self.repo, self.users, self.adapters = repo, users, adapters

    def adapter(self, kind: str) -> ApprovalChannel:
        if kind not in self.adapters: raise AppError("CHANNEL_KIND_UNSUPPORTED", kind=kind)
        return self.adapters[kind]

    @staticmethod
    def secrets(c: ChannelRow) -> dict: return json.loads(crypto.decrypt(c.secrets))

    def is_admin(self, uid: str) -> bool:
        u = self.users.get_by_id(uid); return bool(u and u.is_admin)

    @staticmethod
    def usable(uid: str, c: Optional[ChannelRow]) -> bool:
        """May this user send through the channel (own personal channel or any org channel)?"""
        return c is not None and (c.scope == "org" or c.owner == uid)

    def _writable(self, uid: str, cid: str) -> ChannelRow:
        c = self.repo.channel(cid)
        if not self.usable(uid, c): raise AppError("CHANNEL_NOT_FOUND")
        if c.scope == "org" and not self.is_admin(uid): raise AppError("CHANNEL_ADMIN_REQUIRED")
        return c

    # ---- lookups used by approvals and identity codes ----
    def for_node(self, owner: str, cfg: dict) -> Optional[ChannelRow]:
        """The connection a Human node's `approval` config points at: `channel_id` (personal or org), or the legacy
        `channel` kind (the owner's personal connection, else the org one)."""
        if cfg.get("channel_id"):
            c = self.repo.channel(str(cfg["channel_id"]))
            return c if self.usable(owner, c) and c.kind in self.adapters else None
        kind = cfg.get("channel")
        if kind not in self.adapters: return None
        return self.repo.find_channel(owner, kind, "user") or self.repo.org_channel(kind)

    def dm_channel(self, uid: str, kind: str) -> Optional[tuple[ApprovalChannel, dict]]:
        """(adapter, secrets) able to DM this user's chat account: their personal connection, else the org one."""
        if kind not in self.adapters: return None
        c = self.repo.find_channel(uid, kind, "user") or self.repo.org_channel(kind)
        return (self.adapters[kind], self.secrets(c)) if c is not None else None

    # ---- API ----
    def public(self, c: ChannelRow, uid: str, admin: bool) -> dict:
        base = config.public_url(); path = callback_path(c.kind, c.id)
        return {"id": c.id, "kind": c.kind, "scope": c.scope, "name": c.name, "hint": c.hint, "created": c.created,
                "editable": c.owner == uid if c.scope == "user" else admin,
                "callback_url": (base + path) if base else None, "callback_path": path}

    def list(self, uid: str) -> dict:
        admin = self.is_admin(uid)
        return {"kinds": [{"kind": k, "fields": list(a.fields), "optional": list(a.optional)} for k, a in self.adapters.items()],
                "channels": [self.public(c, uid, admin) for c in self.repo.channels_visible(uid) if c.kind in self.adapters],
                "public_url": config.public_url() or None, "is_admin": admin}

    def _values(self, a: ApprovalChannel, body: dict) -> tuple[str, str]:
        vals = a.prepare(body)
        return crypto.encrypt(json.dumps(vals)), crypto.mask(vals[a.hint_field])

    @staticmethod
    def _name(body: dict) -> Optional[str]:
        n = body.get("name"); return n.strip()[:80] or None if isinstance(n, str) else None

    def create(self, uid: str, body) -> dict:
        """{kind, scope?, name?, ...secret fields}. One connection per owner, scope and kind: saving again replaces
        its secrets (same id, same callback URL)."""
        body = body if isinstance(body, dict) else {}
        a = self.adapter(str(body.get("kind") or "")); scope = body.get("scope") or "user"
        if scope not in SCOPES: raise AppError("CHANNEL_CONFIG_INVALID", field="scope")
        if scope == "org" and not self.is_admin(uid): raise AppError("CHANNEL_ADMIN_REQUIRED")
        enc, hint = self._values(a, body)
        old = self.repo.find_channel(uid, a.kind, scope)
        row = ChannelRow(id=old.id if old else self.repo.new_id(), owner=uid, kind=a.kind, scope=scope, name=self._name(body) or (old.name if old else None),
                         secrets=enc, hint=hint, created=old.created if old else time.time())
        return self.public(self.repo.save_channel(row), uid, self.is_admin(uid))

    def update(self, uid: str, cid: str, body) -> dict:
        """Replace the secrets (all required fields) and/or the name."""
        body = body if isinstance(body, dict) else {}; c = self._writable(uid, cid); a = self.adapter(c.kind)
        if any(body.get(f) for f in a.fields): c.secrets, c.hint = self._values(a, body)
        if "name" in body: c.name = self._name(body)
        return self.public(self.repo.save_channel(c), uid, self.is_admin(uid))

    def delete(self, uid: str, cid: str) -> dict:
        self._writable(uid, cid); self.repo.delete_channel(cid); return {"ok": True}

    def register_webhook(self, uid: str, cid: str) -> dict:
        c = self._writable(uid, cid)
        base = config.public_url()
        if not base.startswith("https://"): raise AppError("CHANNEL_PUBLIC_URL_REQUIRED")
        url = base + callback_path(c.kind, c.id)
        return {"callback_url": url, **self.adapter(c.kind).register(self.secrets(c), url)}
