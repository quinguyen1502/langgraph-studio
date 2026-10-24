"""Sandbox service: `python -m app.sandbox_service` (image docker/studio-sandbox). A studio with
STUDIO_CODE_RUNTIME=remote sends each Code call here instead of running it next to its database and secrets.

What it does: runs the call with the subprocess runtime (engine/code_runtime.py SubprocessRunner): an empty
environment, a temporary folder, rlimits, the time limit, and (as root with STUDIO_CODE_RUN_AS) its own unprivileged
uid per concurrent call. Python gets the no-network/no-process audit hook (STUDIO_CODE_NO_NETWORK=1); TypeScript runs
on Deno with no permissions at all. What it does not do: kernel-level isolation. Code shares this container's kernel,
file system (read-only for its uid) and, unless the platform blocks egress, its network for anything that escapes the
audit hook. Deploy it with no secrets in its environment, ideally on a network without internet access.

STUDIO_SANDBOX_TOKEN (16+ characters, required) authenticates the studio. Endpoints: GET /healthz (no auth),
GET /v1/info, POST /v1/run, POST /v1/runs/<id>/cancel; responses use the studio's envelope."""
from __future__ import annotations
import hmac, json, os, socket, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional
from .core import config
from .core.errors import AppError
from .core.logging import get_logger
from .engine import code_languages as langs, code_runtime

log = get_logger("sandbox")
BODY_MAX = code_runtime.SOURCE_MAX + code_runtime.STATE_MAX + 64 * 1024
RUNNER = code_runtime.SubprocessRunner()


class Sandbox:
    """The service's state: the token and the calls in flight (for cancel)."""

    def __init__(self, token: str) -> None:
        if len(token) < 16: raise SystemExit("STUDIO_SANDBOX_TOKEN must be set (16 characters or more)")
        self.token = token; self.running: Dict[str, threading.Event] = {}; self.lock = threading.Lock()

    def authorised(self, header: Optional[str]) -> bool:
        return hmac.compare_digest((header or "").encode(), f"Bearer {self.token}".encode())

    def info(self) -> dict:
        return {"languages": {x: RUNNER.problem(langs.LANGUAGES[x]) for x in langs.enabled()},
                "limits": {"seconds": config.code_max_seconds(), "memory": config.code_memory(), "concurrency": config.code_concurrency()}}

    def run(self, body: dict) -> dict:
        run_id, payload = str(body.get("id") or ""), body.get("payload")
        if not run_id or not isinstance(payload, str): raise AppError("VALIDATION_ERROR", details=[{"field": "payload", "message": "id and payload are required"}])
        lang = langs.get(body.get("language"))
        try: seconds = min(float(body.get("seconds") or config.code_max_seconds()), float(config.code_max_seconds()))
        except (TypeError, ValueError): seconds = float(config.code_max_seconds())
        stop = threading.Event()
        with self.lock: self.running[run_id] = stop
        slot = code_runtime._slot()
        if not slot.acquire(timeout=seconds): raise AppError("CODE_TIMEOUT", node="code", seconds=f"{seconds:g}")
        try: out, err, code, stopped = RUNNER.exchange(lang, payload, seconds, stop.is_set)
        finally:
            slot.release()
            with self.lock: self.running.pop(run_id, None)
        return {"stdout": out, "stderr": err[-4096:], "returncode": code, "stopped": stopped}

    def cancel(self, run_id: str) -> dict:
        with self.lock: ev = self.running.get(run_id)
        if ev is None: raise AppError("NOT_FOUND")
        ev.set(); return {"cancelled": True}


def _fail(code: str) -> Any: raise AppError(code)


def handler(box: Sandbox) -> type:
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, fmt: str, *args: Any) -> None: log.debug(fmt, *args)

        def _send(self, status: int, env: dict) -> None:
            data = json.dumps(env, ensure_ascii=False).encode()
            self.send_response(status); self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)

        def _handle(self, fn) -> None:
            try: self._send(200, {"success": True, "data": fn(), "error": None})
            except AppError as e: self._send(e.status, {"success": False, "data": None, "error": e.to_dict()})
            except Exception as e:  # never a traceback to the caller
                log.exception("sandbox call failed: %s", e)
                self._send(500, {"success": False, "data": None, "error": AppError("INTERNAL_ERROR").to_dict()})

        def _authorised(self) -> bool:
            if box.authorised(self.headers.get("Authorization")): return True
            self._send(401, {"success": False, "data": None, "error": AppError("AUTH_TOKEN_INVALID").to_dict()}); return False

        def do_GET(self) -> None:
            if self.path == "/healthz": return self._handle(lambda: {"ok": True})
            if not self._authorised(): return
            if self.path == "/v1/info": return self._handle(box.info)
            self._handle(lambda: _fail("NOT_FOUND"))

        def do_POST(self) -> None:
            if not self._authorised(): return
            size = int(self.headers.get("Content-Length") or 0)
            if size > BODY_MAX: self.close_connection = True; return self._send(413, {"success": False, "data": None, "error": AppError("PAYLOAD_TOO_LARGE").to_dict()})
            raw = self.rfile.read(size) if size else b"{}"
            try: body = json.loads(raw or b"{}")
            except ValueError: body = None
            if not isinstance(body, dict): return self._handle(lambda: _fail("VALIDATION_ERROR"))
            if self.path == "/v1/run": return self._handle(lambda: box.run(body))
            if self.path.startswith("/v1/runs/") and self.path.endswith("/cancel"):
                return self._handle(lambda: box.cancel(self.path[len("/v1/runs/"):-len("/cancel")]))
            self._handle(lambda: _fail("NOT_FOUND"))
    return Handler


def make_server(host: str, port: int, token: str) -> ThreadingHTTPServer:
    class Server(ThreadingHTTPServer):
        address_family = socket.AF_INET6 if ":" in host else socket.AF_INET
        daemon_threads = True
    return Server((host, port), handler(Sandbox(token)))


def main() -> None:
    import logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    srv = make_server(os.environ.get("STUDIO_SANDBOX_HOST", "0.0.0.0"), int(os.environ.get("PORT", "8080")), config.sandbox_token())
    log.info("sandbox service on %s:%s (languages: %s, no network: %s, run as: %s)", *srv.server_address[:2],
             ",".join(langs.enabled()), config.code_no_network(), config.code_run_as())
    srv.serve_forever()


if __name__ == "__main__":
    main()
