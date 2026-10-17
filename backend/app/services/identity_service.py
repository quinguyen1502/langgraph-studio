"""Linking a chat account to a studio user, proven by a one-time code (TASK-0022 follow-up, DEC-0019).

link -> the account is stored unverified; send_code -> the bot DMs a 6-digit code to that account; verify -> the
user types it back. Only verified links map button presses to studio users. Codes are stored as an HMAC, expire
(STUDIO_IDENTITY_CODE_TTL), allow STUDIO_IDENTITY_CODE_ATTEMPTS wrong tries and can be resent every
STUDIO_IDENTITY_CODE_RESEND seconds. An account has at most one verified owner (IDENTITY_TAKEN).
"""
import hashlib, hmac, secrets as pysecrets, time
from typing import Callable, Optional
from ..core import config, crypto
from ..core.errors import AppError
from ..repositories import ApprovalRepository, UserRepository
from .approval_channels import ApprovalChannel
from .approval_channels.messages import lang_of, text


class IdentityService:
    def __init__(self, repo: ApprovalRepository, users: UserRepository, adapters: dict[str, ApprovalChannel],
                 dm_channel: Callable[[str, str], Optional[tuple[ApprovalChannel, dict]]]):
        """dm_channel(uid, kind) -> (adapter, secrets) of a channel that can DM this user, or None."""
        self.repo, self.users, self.adapters, self.dm_channel = repo, users, adapters, dm_channel

    def _adapter(self, kind: str) -> ApprovalChannel:
        if kind not in self.adapters: raise AppError("CHANNEL_KIND_UNSUPPORTED", kind=kind)
        return self.adapters[kind]

    @staticmethod
    def _hash(uid: str, kind: str, external_id: str, code: str) -> str:
        return hmac.new(crypto.derive_key("identity-code"), f"{uid}:{kind}:{external_id}:{code}".encode(), hashlib.sha256).hexdigest()

    def get(self, uid: str) -> dict:
        mine, now = self.repo.identities(uid), time.time()
        def view(i):
            if i is None: return None
            pending = bool(i.code_hash) and not i.verified_at and (i.code_expires or 0) > now
            return {"external_id": i.external_id, "verified": i.verified_at is not None, "code_pending": pending,
                    "code_expires": i.code_expires if pending else None}
        return {k: view(mine.get(k)) for k in self.adapters}

    def link(self, uid: str, body) -> dict:
        """{kind: external id | "" (unlink)}. A new or changed account starts unverified."""
        if not isinstance(body, dict) or not body: raise AppError("IDENTITY_INVALID", kind="channel")
        for kind, v in body.items():
            a = self._adapter(kind); v = v.strip() if isinstance(v, str) else v
            if v and (not isinstance(v, str) or not a.valid_identity(v)): raise AppError("IDENTITY_INVALID", kind=a.label)
            self.repo.put_identity(uid, kind, v or None)
        return self.get(uid)

    def send_code(self, uid: str, kind: str) -> dict:
        a = self._adapter(kind); i = self.repo.identity(uid, kind)
        if i is None: raise AppError("IDENTITY_NOT_LINKED", kind=a.label)
        if i.verified_at: return self.get(uid)
        now = time.time(); wait = int((i.code_sent_at or 0) + config.identity_code_resend() - now + 0.999)
        if wait > 0: raise AppError("RATE_LIMITED", headers={"Retry-After": str(wait)}, retry_after=wait)
        via = self.dm_channel(uid, kind)
        if via is None: raise AppError("CHANNEL_NOT_FOUND")
        code = f"{pysecrets.randbelow(10**6):06d}"
        via[0].send_dm(via[1], i.external_id, text(lang_of(self.users.get_by_id(uid)), "code", code=code, minutes=int(config.identity_code_ttl() // 60)))  # 502 CHANNEL_API_FAILED (e.g. the user never started the bot)
        self.repo.set_identity(uid, kind, code_hash=self._hash(uid, kind, i.external_id, code), code_expires=now + config.identity_code_ttl(),
                               code_sent_at=now, code_attempts=0)
        return self.get(uid)

    def verify(self, uid: str, kind: str, body) -> dict:
        a = self._adapter(kind); i = self.repo.identity(uid, kind)
        code = str((body or {}).get("code") or "").strip() if isinstance(body, dict) else ""
        if i is None: raise AppError("IDENTITY_NOT_LINKED", kind=a.label)
        if i.verified_at: return self.get(uid)
        if not i.code_hash or time.time() > (i.code_expires or 0): raise AppError("IDENTITY_CODE_EXPIRED")
        limit = config.identity_code_attempts()
        if i.code_attempts >= limit: raise AppError("IDENTITY_CODE_ATTEMPTS")
        if not hmac.compare_digest(self._hash(uid, kind, i.external_id, code), i.code_hash):
            left = max(0, limit - self.repo.count_attempt(uid, kind))
            if left == 0: raise AppError("IDENTITY_CODE_ATTEMPTS")
            raise AppError("IDENTITY_CODE_INVALID", left=left)
        other = self.repo.user_for(kind, i.external_id)
        if other is not None and other != uid: raise AppError("IDENTITY_TAKEN", kind=a.label)
        self.repo.set_identity(uid, kind, verified_at=time.time(), code_hash=None, code_expires=None, code_attempts=0)
        return self.get(uid)
