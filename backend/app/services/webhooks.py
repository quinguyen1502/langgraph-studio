"""Result webhooks (TASK-0007, hardened in TASK-0019 / DEC-0016).

- SSRF guard: http(s) only; private / loopback / link-local / reserved / multicast targets are refused
  unless STUDIO_ALLOW_PRIVATE_CALLBACKS=1.
- DNS-rebinding safe: the host is resolved ONCE at delivery time, every address is validated, and the request
  connects to that pinned IP (Host header + TLS SNI/certificate check still use the original hostname).
- Signed: `X-Studio-Signature: t=<unix ts>,v1=<hex HMAC-SHA256(secret, "<ts>.<raw body>")>` with the token's
  signing secret (shown once when the token is created). `verify_signature` is the reference check.
"""
import hashlib, hmac, ipaddress, json, socket, time
from typing import Optional
from urllib.parse import urlparse, urlunparse
import httpx
from ..core import config
from ..core.errors import AppError
from ..core.logging import get_logger

log = get_logger("webhooks")
ATTEMPTS = 2
SIGNATURE_HEADER = "X-Studio-Signature"
TOLERANCE_S = 300  # receivers should reject signatures older than this (replay protection)


def http_client() -> httpx.Client:
    """Factory for webhook calls (tests replace it with a MockTransport client)."""
    return httpx.Client(timeout=10, follow_redirects=False)  # a redirect could point anywhere: never follow


def _blocked(ip: ipaddress._BaseAddress) -> bool:
    return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified


def resolve(url: Optional[str]) -> tuple[str, str]:
    """Validate `url` and resolve its host once. Returns (url, pinned_ip). Raises CALLBACK_URL_INVALID."""
    u = urlparse(url or "")
    if u.scheme not in ("http", "https") or not u.hostname: raise AppError("CALLBACK_URL_INVALID")
    try: addrs = [ai[4][0].split("%")[0] for ai in socket.getaddrinfo(u.hostname, u.port or (443 if u.scheme == "https" else 80), proto=socket.IPPROTO_TCP)]
    except (OSError, UnicodeError): raise AppError("CALLBACK_URL_INVALID") from None
    if not addrs: raise AppError("CALLBACK_URL_INVALID")
    if not config.allow_private_callbacks() and any(_blocked(ipaddress.ip_address(a)) for a in addrs):
        raise AppError("CALLBACK_URL_INVALID")
    return url, addrs[0]


def check_callback_url(url: Optional[str]) -> Optional[str]:
    """Early validation when the run is queued (the address is resolved and checked again at delivery)."""
    return resolve(url)[0] if url else None


def pinned_request(url: str, ip: str) -> tuple[str, dict, dict]:
    """(url with the IP as host, headers, httpx extensions) so the connection goes to the validated IP."""
    u = urlparse(url); host = u.hostname or ""
    ip_host = f"[{ip}]" if ":" in ip else ip
    netloc = ip_host + (f":{u.port}" if u.port else "")
    headers = {"Host": u.netloc.rsplit("@", 1)[-1]}
    ext = {"sni_hostname": host} if u.scheme == "https" else {}
    return urlunparse(u._replace(netloc=netloc)), headers, ext


def sign(secret: str, body: bytes, ts: Optional[int] = None) -> str:
    ts = int(ts if ts is not None else time.time())
    mac = hmac.new(secret.encode(), f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
    return f"t={ts},v1={mac}"


def verify_signature(secret: str, header: str, body: bytes, tolerance: int = TOLERANCE_S, now: Optional[float] = None) -> bool:
    """Reference receiver-side check (documented in the README)."""
    try:
        parts = dict(p.split("=", 1) for p in (header or "").split(","))
        ts = int(parts["t"])
    except (ValueError, KeyError):
        return False
    if abs((now or time.time()) - ts) > tolerance: return False
    expected = sign(secret, body, ts).split("v1=", 1)[1]
    return hmac.compare_digest(expected, parts.get("v1", ""))


def deliver(url: str, payload: dict, secret: Optional[str] = None) -> bool:
    """POST the result to the caller's webhook (pinned IP, signed when a secret is known); one retry. Never raises."""
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
    for attempt in range(ATTEMPTS):
        try:
            _, ip = resolve(url)
            target, headers, ext = pinned_request(url, ip)
            headers.update({"Content-Type": "application/json", "X-Studio-Event": "run.finished"})
            if secret: headers[SIGNATURE_HEADER] = sign(secret, body)
            with http_client() as c:
                r = c.send(c.build_request("POST", target, content=body, headers=headers, extensions=ext))
            if r.status_code < 400: return True
            log.warning("callback %s returned HTTP %s", url, r.status_code)
        except AppError:
            log.warning("callback %s refused (address not allowed or unresolvable)", url); return False
        except httpx.HTTPError as e:
            log.warning("callback %s failed: %s", url, type(e).__name__)
        if attempt + 1 < ATTEMPTS: time.sleep(1)
    return False
