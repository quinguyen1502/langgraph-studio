"""Encryption at rest for secrets (Fernet = AES-128-CBC + HMAC-SHA256).

Key source (first match):
  1. STUDIO_SECRET_KEY env var (urlsafe base64 32-byte Fernet key)
  2. key file STUDIO_SECRET_KEY_FILE (default ~/.langgraph-studio/secret.key), created with 0600 on first use.
"""
from __future__ import annotations
import os
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken

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
