"""Per-user LLM provider credentials: create/list/delete and the run-time resolver.

Secrets are encrypted before they reach the repository and are only decrypted by `resolver()`."""
import time, uuid
from typing import Any, Callable, Dict
from ..core import crypto
from ..core.errors import AppError
from ..engine.llm import PROVIDERS
from ..models import Credential
from ..repositories import CredentialRepository


def public(c: Credential) -> Dict[str, Any]:
    return {"id": c.id, "name": c.name, "provider": c.provider, "base_url": c.base_url, "hint": c.hint, "created": c.created}


class CredentialService:
    def __init__(self, repo: CredentialRepository): self.repo = repo

    @staticmethod
    def providers() -> list[dict]:
        return [{"id": k, **v} for k, v in PROVIDERS.items()]

    def list(self, uid: str) -> list[dict]:
        return [public(c) for c in self.repo.list_for_owner(uid)]

    def create(self, uid: str, name: str, provider: str, api_key: str, base_url: str | None) -> dict:
        if provider not in PROVIDERS: raise AppError("CREDENTIAL_PROVIDER_UNSUPPORTED", provider=provider)
        key = api_key.strip()
        if not key: raise AppError("CREDENTIAL_KEY_REQUIRED")
        if base_url and not base_url.startswith(("https://", "http://")): raise AppError("CREDENTIAL_BASE_URL_INVALID")
        c = Credential(id=uuid.uuid4().hex[:10], owner=uid, name=name.strip() or provider, provider=provider,
                       base_url=(base_url or "").strip() or None, secret=crypto.encrypt(key), hint=crypto.mask(key), created=time.time())
        return public(self.repo.add(c))

    def delete(self, cid: str, uid: str) -> dict:
        if not self.repo.delete_owned(cid, uid): raise AppError("CREDENTIAL_NOT_FOUND")
        return {"ok": True}

    def resolve(self, uid: str, cid: str) -> Dict[str, Any]:
        """Decrypted credential for runtime use only. Raises CREDENTIAL_NOT_FOUND if missing or not owned."""
        c = self.repo.get_owned(cid, uid)
        if c is None: raise AppError("CREDENTIAL_NOT_FOUND", details={"credential_id": cid})
        return {"provider": c.provider, "base_url": c.base_url or PROVIDERS[c.provider]["default_base_url"],
                "api_key": crypto.decrypt(c.secret or ""), "name": c.name}

    def resolver(self, uid: str) -> Callable[[str], Dict[str, Any]]:
        """Credential lookup bound to one user, handed to the run engine (`run_stream(resolve=...)`)."""
        return lambda cid: self.resolve(uid, cid)
