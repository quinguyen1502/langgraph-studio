"""Encrypted-at-rest LLM provider credentials (Fernet / AES-128-CBC + HMAC-SHA256).

Key source (first match):
  1. STUDIO_SECRET_KEY env var (urlsafe base64 32-byte Fernet key)
  2. key file STUDIO_SECRET_KEY_FILE (default ~/.langgraph-studio/secret.key), created with 0600 on first use.
Secrets are only decrypted server-side at run time and never returned by the API."""
from __future__ import annotations
import os, time, uuid
from typing import Any, Dict, List, Optional
from cryptography.fernet import Fernet, InvalidToken

PROVIDERS = {
    "openai": {"label": "OpenAI / OpenAI-compatible", "default_base_url": "https://api.openai.com/v1"},
    "anthropic": {"label": "Anthropic", "default_base_url": "https://api.anthropic.com"},
}
_fernet: Optional[Fernet] = None


def _key() -> bytes:
    env = os.environ.get("STUDIO_SECRET_KEY")
    if env: return env.encode()
    path = os.path.expanduser(os.environ.get("STUDIO_SECRET_KEY_FILE") or "~/.langgraph-studio/secret.key")
    if os.path.exists(path): return open(path, "rb").read().strip()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    k = Fernet.generate_key()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as f: f.write(k)
    return k


def fernet() -> Fernet:
    global _fernet
    if _fernet is None: _fernet = Fernet(_key())
    return _fernet


def encrypt(secret: str) -> str: return fernet().encrypt(secret.encode()).decode()


def decrypt(token: str) -> str:
    try: return fernet().decrypt(token.encode()).decode()
    except InvalidToken: raise ValueError("Không giải mã được credential (secret key đã thay đổi?)")


def mask(secret: str) -> str: return ("•" * 4) + secret[-4:] if len(secret) >= 8 else "•" * 4


def init_table(c):
    c.execute("CREATE TABLE IF NOT EXISTS credentials(id TEXT PRIMARY KEY, owner TEXT, name TEXT, provider TEXT, base_url TEXT, secret TEXT, hint TEXT, created REAL)")


def public(r) -> Dict[str, Any]:
    return {"id": r["id"], "name": r["name"], "provider": r["provider"], "base_url": r["base_url"], "hint": r["hint"], "created": r["created"]}


def create(c, owner: str, name: str, provider: str, api_key: str, base_url: Optional[str]) -> Dict[str, Any]:
    if provider not in PROVIDERS: raise ValueError(f"Provider không hỗ trợ: {provider}")
    if not api_key.strip(): raise ValueError("API key trống")
    if base_url and not base_url.startswith(("https://", "http://")): raise ValueError("Base URL phải bắt đầu bằng http(s)://")
    cid = uuid.uuid4().hex[:10]
    c.execute("INSERT INTO credentials VALUES(?,?,?,?,?,?,?,?)",
              (cid, owner, name.strip() or provider, provider, (base_url or "").strip() or None, encrypt(api_key.strip()), mask(api_key.strip()), time.time()))
    return public(c.execute("SELECT * FROM credentials WHERE id=?", (cid,)).fetchone())


def list_for(c, owner: str) -> List[Dict[str, Any]]:
    return [public(r) for r in c.execute("SELECT * FROM credentials WHERE owner=? ORDER BY created DESC", (owner,))]


def resolve(c, owner: str, cid: str) -> Dict[str, Any]:
    """Decrypted credential for runtime use only. Raises if missing or not owned."""
    r = c.execute("SELECT * FROM credentials WHERE id=? AND owner=?", (cid, owner)).fetchone()
    if not r: raise ValueError(f"Credential '{cid}' không tồn tại hoặc không thuộc về bạn")
    return {"provider": r["provider"], "base_url": r["base_url"] or PROVIDERS[r["provider"]]["default_base_url"], "api_key": decrypt(r["secret"]), "name": r["name"]}
