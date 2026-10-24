"""Encryption at rest for secrets (Fernet = AES-128-CBC + HMAC-SHA256).

Key source (first match):
  1. STUDIO_SECRET_KEY env var: a Fernet key (urlsafe base64, 32 bytes) is used as is; any other value (a PaaS
     generated secret such as Heroku's 64 hex characters) is stretched to one with SHA-256.
  2. key file STUDIO_SECRET_KEY_FILE (default ~/.superstep/secret.key, see config.home_dir), created with 0600 on first use.
     Production (STUDIO_ENV=production) refuses to create one: set STUDIO_SECRET_KEY (check_key).
"""
from __future__ import annotations
import base64, hashlib, hmac, os
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken
from . import config
from .errors import AppError

_fernet: Optional[Fernet] = None


def _key_path() -> str:
    return os.path.expanduser(os.environ.get("STUDIO_SECRET_KEY_FILE") or os.path.join(config.home_dir(), "secret.key"))


def as_fernet_key(raw: str) -> bytes:
    try: Fernet(raw.encode()); return raw.encode()
    except ValueError: return base64.urlsafe_b64encode(hashlib.sha256(raw.encode()).digest())


def check_key() -> None:
    """Start-up check: production needs STUDIO_SECRET_KEY, unless a key file from an earlier start already exists.
    A key generated into an ephemeral PaaS file system would make every stored credential unreadable after a restart."""
    if config.IS_PROD and not os.environ.get("STUDIO_SECRET_KEY") and not os.path.exists(_key_path()):
        raise RuntimeError("STUDIO_SECRET_KEY must be set when STUDIO_ENV=production")


def _key() -> bytes:
    env = os.environ.get("STUDIO_SECRET_KEY")
    if env: return as_fernet_key(env)
    path = _key_path()
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
    except InvalidToken: raise AppError("CREDENTIAL_DECRYPT_FAILED")


def derive_key(purpose: str) -> bytes:
    """A separate HMAC key per purpose (e.g. signing approval tokens), derived from the same secret key.
    The prefix keeps the v0.1.0 name: changing it would invalidate every pending approval link and identity code."""
    return hmac.new(_key(), b"langgraph-studio:" + purpose.encode(), hashlib.sha256).digest()


def mask(secret: str) -> str: return ("•" * 4) + secret[-4:] if len(secret) >= 8 else "•" * 4
