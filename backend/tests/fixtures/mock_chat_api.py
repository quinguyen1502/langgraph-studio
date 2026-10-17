"""Fake Slack + Telegram Web APIs for the e2e suite (TASK-0022). Records every call; GET /_messages lists them.

Run: python mock_chat_api.py [port]  (default 8111). Point SLACK_API_URL=http://127.0.0.1:8111/slack and
TELEGRAM_API_URL=http://127.0.0.1:8111/telegram at it. A bot token xoxb-<n>-<TEAM>-... answers auth.test with team <TEAM>.
"""
import json, sys, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

CALLS: list[dict] = []


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _send(self, data, status=200):
        b = json.dumps(data).encode(); self.send_response(status); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        if self.path.startswith("/_messages"): return self._send(CALLS)
        if self.path.startswith("/health"): return self._send({"ok": True})
        self._send({"ok": False}, 404)

    def do_DELETE(self):
        CALLS.clear(); self._send({"ok": True})

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0); raw = self.rfile.read(n) if n else b"{}"
        try: body = json.loads(raw or b"{}")
        except ValueError: body = {}
        method = self.path.rstrip("/").rsplit("/", 1)[-1]; auth = self.headers.get("Authorization", "")
        CALLS.append({"path": self.path, "method": method, "body": body, "at": time.time()})
        if self.path.startswith("/slack/"):
            if method == "auth.test":
                parts = auth.removeprefix("Bearer ").split("-")
                team = parts[2] if len(parts) > 3 else "T0E2E"
                return self._send({"ok": True, "team": f"Workspace {team}", "team_id": team, "user_id": "UBOT", "bot_id": "BBOT"})
            if method == "chat.postMessage": return self._send({"ok": True, "channel": body.get("channel"), "ts": f"{time.time():.6f}"})
            return self._send({"ok": True})
        if self.path.startswith("/telegram/"):
            if method == "getMe": return self._send({"ok": True, "result": {"id": 1, "is_bot": True, "username": "studio_e2e_bot", "first_name": "Studio"}})
            if method == "sendMessage": return self._send({"ok": True, "result": {"message_id": len(CALLS), "chat": {"id": body.get("chat_id")}}})
            return self._send({"ok": True, "result": True})
        self._send({"ok": False, "error": "unknown"}, 404)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8111
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
