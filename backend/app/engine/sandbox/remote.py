"""Client of the sandbox service (STUDIO_CODE_RUNTIME=remote): `app.sandbox_service` runs Code calls in a separate
container that holds none of the studio's secrets. Bearer STUDIO_SANDBOX_TOKEN on every call.

POST /v1/run {id, language, payload, seconds} -> {stdout, stderr, returncode, stopped}; POST /v1/runs/<id>/cancel;
GET /v1/info -> {languages: {id: problem | null}}. Responses use the studio's envelope ({success, data, error})."""
from __future__ import annotations
import threading, time, uuid
from typing import Any, Callable, Dict, Optional
import httpx
from ...core import config
from ...core.errors import AppError

CHECK_TTL = 30.0
GRACE = 15.0  # the service enforces the time limit; the client waits this much longer for its answer
_info: Dict[str, tuple[float, Optional[str], Dict[str, Any]]] = {}  # url -> (when, problem, languages)


def _request(method: str, path: str, body: Optional[dict] = None, timeout: float = 10.0) -> Any:
    url, token = config.sandbox_url(), config.sandbox_token()
    r = httpx.request(method, url + path, json=body, timeout=timeout, headers={"Authorization": f"Bearer {token}"})
    try: env = r.json()
    except ValueError: raise RuntimeError(f"HTTP {r.status_code} from the sandbox service") from None
    if r.status_code == 401: raise PermissionError("the sandbox service refused STUDIO_SANDBOX_TOKEN")
    if not env.get("success"): raise RuntimeError((env.get("error") or {}).get("message") or f"HTTP {r.status_code}")
    return env.get("data")


def problem(language: str) -> Optional[str]:
    """Why `language` cannot run on the sandbox service now, or None. Checked at most every 30 s."""
    url = config.sandbox_url()
    if not url: return "STUDIO_SANDBOX_URL is not set"
    if len(config.sandbox_token()) < 16: return "STUDIO_SANDBOX_TOKEN is not set (16 characters or more)"
    hit = _info.get(url)
    if not hit or time.monotonic() - hit[0] >= CHECK_TTL:
        try: why, langs = None, (_request("GET", "/v1/info") or {}).get("languages") or {}
        except PermissionError as e: why, langs = str(e), {}
        except (httpx.HTTPError, RuntimeError) as e: why, langs = f"the sandbox service at {url} did not answer ({str(e)[:200]})", {}
        hit = _info[url] = (time.monotonic(), why, langs)
    if hit[1]: return hit[1]
    if language not in hit[2]: return f"the sandbox service does not offer {language}"
    return hit[2][language]


def forget() -> None: _info.clear()  # after a failed call, check again on the next one


def run(language: str, payload: str, seconds: float, cancelled: Optional[Callable[[], bool]]) -> tuple[str, str, int, str]:
    """One call. A cancel is forwarded to the service; a service that does not answer is CODE_RUNTIME_UNAVAILABLE."""
    run_id = uuid.uuid4().hex
    box: Dict[str, Any] = {}

    def call() -> None:
        try: box["data"] = _request("POST", "/v1/run", {"id": run_id, "language": language, "payload": payload, "seconds": seconds},
                                    timeout=seconds + GRACE)
        except Exception as e: box["error"] = e
    t = threading.Thread(target=call, daemon=True); t.start()
    while t.is_alive():
        t.join(0.25)
        if t.is_alive() and cancelled is not None and cancelled():
            try: _request("POST", f"/v1/runs/{run_id}/cancel", timeout=5)
            except Exception: pass  # the service's own time limit still ends it
            return "", "", -9, "cancelled"
    if "error" in box:
        forget(); e = box["error"]
        reason = "the sandbox service did not answer in time" if isinstance(e, httpx.TimeoutException) else str(e)[:300]
        raise AppError("CODE_RUNTIME_UNAVAILABLE", reason=reason)
    d = box.get("data") or {}
    return d.get("stdout") or "", d.get("stderr") or "", int(d.get("returncode", -1)), d.get("stopped") or ""
