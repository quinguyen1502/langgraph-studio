"""MCP server registry (TASK-0013): CRUD with encrypted secrets, tool discovery, and the run-time `caller(uid)` port.

Scopes follow approval channels: `user` servers belong to their owner; `org` servers are managed by admins and usable by
everyone. stdio servers start a process on the API host, so they need STUDIO_MCP_STDIO=1 and an admin. HTTP servers must
be public addresses unless STUDIO_MCP_ALLOW_PRIVATE=1, and every connection goes to the address validated just before."""
from __future__ import annotations
import json, re, time, uuid
from typing import Any, Callable, Optional
from ..core import config, crypto
from ..core.errors import AppError
from ..engine import mcp_client
from ..models import McpServer
from ..repositories import McpServerRepository
from ..core.net import pinned_request, public_address

TRANSPORTS = ("stdio", "http")
SCOPES = ("user", "org")
NAME_MAX, ARGS_MAX, SECRETS_MAX, VALUE_MAX = 120, 50, 30, 4096
SECRET_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]{0,63}$")


class McpService:
    def __init__(self, repo: McpServerRepository, is_admin: Callable[[str], bool] = lambda uid: False,
                 org_allowed: Callable[[str], bool] = lambda uid: True):
        self.repo, self.is_admin, self.org_allowed = repo, is_admin, org_allowed

    # ---- views ----
    @staticmethod
    def public(r: McpServer, uid: str, admin: bool) -> dict:
        return {"id": r.id, "name": r.name, "scope": r.scope, "transport": r.transport, "command": r.command,
                "args": json.loads(r.args or "[]"), "url": r.url, "secrets": json.loads(r.secret_hints or "{}"),
                "tools": json.loads(r.tools or "[]"), "tools_at": r.tools_at, "created": r.created,
                "can_edit": r.owner == uid if r.scope == "user" else admin}

    def list(self, uid: str) -> dict:
        admin = self.is_admin(uid)
        return {"servers": [self.public(r, uid, admin) for r in self.repo.visible(uid)], "is_admin": admin,
                "stdio_enabled": config.mcp_stdio_enabled(), "org_usable": self.org_allowed(uid)}

    def _visible(self, sid: str, uid: str) -> McpServer:
        r = self.repo.get(sid)
        if r is None or (r.scope == "user" and r.owner != uid): raise AppError("MCP_SERVER_NOT_FOUND")
        return r

    def _editable(self, sid: str, uid: str) -> McpServer:
        r = self._visible(sid, uid)
        if r.scope == "org" and not self.is_admin(uid): raise AppError("MCP_ADMIN_REQUIRED")
        return r

    # ---- validation ----
    def _check(self, uid: str, scope: str, transport: str, name: str, command: Optional[str], args: Any, url: Optional[str]) -> dict:
        n = (name or "").strip()
        if not n: raise AppError("MCP_NAME_REQUIRED")
        if len(n) > NAME_MAX: raise AppError("MCP_NAME_TOO_LONG", max=NAME_MAX)
        if scope not in SCOPES: raise AppError("MCP_CONFIG_INVALID", field="scope")
        if scope == "org" and not self.is_admin(uid): raise AppError("MCP_ADMIN_REQUIRED")
        if transport not in TRANSPORTS: raise AppError("MCP_TRANSPORT_UNSUPPORTED", transport=transport)
        if transport == "stdio":
            if not config.mcp_stdio_enabled(): raise AppError("MCP_STDIO_DISABLED")
            if not self.is_admin(uid): raise AppError("MCP_ADMIN_REQUIRED")
            cmd = (command or "").strip()
            if not cmd: raise AppError("MCP_CONFIG_INVALID", field="command")
            if not isinstance(args, list) or len(args) > ARGS_MAX or not all(isinstance(a, str) and len(a) <= VALUE_MAX for a in args):
                raise AppError("MCP_CONFIG_INVALID", field="args")
            return {"name": n, "command": cmd, "args": json.dumps(args), "url": None}
        public_address((url or "").strip(), config.mcp_allow_private(), "MCP_URL_INVALID")
        return {"name": n, "command": None, "args": None, "url": (url or "").strip()}

    @staticmethod
    def _secrets(new: Optional[dict], old: dict) -> dict:
        """Merge: a null value keeps the stored value of that name; names not listed are removed."""
        if new is None: return old
        if not isinstance(new, dict) or len(new) > SECRETS_MAX: raise AppError("MCP_CONFIG_INVALID", field="secrets")
        out = {}
        for k, v in new.items():
            if not isinstance(k, str) or not SECRET_NAME.match(k): raise AppError("MCP_CONFIG_INVALID", field="secrets")
            if v is None:
                if k in old: out[k] = old[k]
                continue
            if not isinstance(v, str) or len(v) > VALUE_MAX: raise AppError("MCP_CONFIG_INVALID", field="secrets")
            out[k] = v
        return out

    @staticmethod
    def _stored(r: McpServer) -> dict:
        try: return json.loads(crypto.decrypt(r.secrets)) if r.secrets else {}
        except Exception: raise AppError("CREDENTIAL_DECRYPT_FAILED") from None

    @staticmethod
    def _apply_secrets(r: McpServer, sec: dict) -> None:
        r.secrets = crypto.encrypt(json.dumps(sec)) if sec else None
        r.secret_hints = json.dumps({k: crypto.mask(v) for k, v in sec.items()})

    # ---- CRUD ----
    def create(self, uid: str, name: str, transport: str, scope: str = "user", command: str | None = None, args: Any = None,
               url: str | None = None, secrets: dict | None = None) -> dict:
        v = self._check(uid, scope, transport, name, command, args if args is not None else [], url)
        r = McpServer(id=uuid.uuid4().hex[:10], owner=uid, scope=scope, transport=transport, created=time.time(), **v)
        self._apply_secrets(r, self._secrets(secrets or {}, {}))
        return self.public(self.repo.save(r), uid, self.is_admin(uid))

    def update(self, sid: str, uid: str, name: str, command: str | None = None, args: Any = None, url: str | None = None,
               secrets: dict | None = None) -> dict:
        """Transport and scope are fixed after creation (create a new server instead)."""
        r = self._editable(sid, uid)
        v = self._check(uid, r.scope, r.transport, name, command, args if args is not None else [], url)
        for k, val in v.items(): setattr(r, k, val)
        self._apply_secrets(r, self._secrets(secrets, self._stored(r)))
        r.tools, r.tools_at = None, None  # the configuration changed: discover again
        return self.public(self.repo.save(r), uid, self.is_admin(uid))

    def delete(self, sid: str, uid: str) -> dict:
        self._editable(sid, uid); self.repo.delete(sid); return {"ok": True}

    # ---- connection ----
    def _spec(self, r: McpServer) -> dict:
        sec = self._stored(r)
        if r.transport == "stdio":
            if not config.mcp_stdio_enabled(): raise AppError("MCP_STDIO_DISABLED")
            return {"transport": "stdio", "command": r.command, "args": json.loads(r.args or "[]"), "env": sec}
        def pin(u: str):  # re-validated on every request: DNS changes cannot redirect the call to a private address
            url, ip = public_address(u, config.mcp_allow_private(), "MCP_URL_INVALID")
            return pinned_request(url, ip)
        return {"transport": "http", "url": r.url, "headers": sec, "pin": pin}

    def discover(self, sid: str, uid: str) -> dict:
        r = self._visible(sid, uid)
        try: tools = mcp_client.list_tools(self._spec(r), config.mcp_timeout())
        except mcp_client.McpError as e: raise AppError("MCP_CONNECT_FAILED", reason=str(e)) from None
        r.tools, r.tools_at = json.dumps(tools), time.time(); self.repo.save(r)
        return self.public(r, uid, self.is_admin(uid))

    @staticmethod
    def coerce(args: dict, schema: dict) -> dict:
        """Form inputs are strings: convert them to the types the tool's input schema declares."""
        props = (schema or {}).get("properties") or {}
        out = {}
        for k, v in (args or {}).items():
            t = (props.get(k) or {}).get("type")
            if isinstance(v, str):
                s = v.strip()
                if s == "" and k not in ((schema or {}).get("required") or []): continue  # optional and left empty
                try:
                    if t == "integer": v = int(s)
                    elif t == "number": v = float(s)
                    elif t == "boolean": v = s.lower() in ("1", "true", "yes", "on")
                    elif t in ("object", "array"): v = json.loads(s)
                except ValueError: raise AppError("MCP_ARGUMENT_INVALID", name=k, type=t) from None
            out[k] = v
        return out

    def call(self, uid: str, sid: str, tool: str, args: dict, org_allowed: bool = True) -> Any:
        r = self._visible(sid, uid)
        if r.scope == "org" and not org_allowed: raise AppError("ORG_RESOURCE_NOT_ALLOWED", kind="MCP server")  # policy, TASK-0029
        tools = {t["name"]: t for t in json.loads(r.tools or "[]")}
        if tool not in tools:
            tools = {t["name"]: t for t in self.discover(sid, uid)["tools"]}
            if tool not in tools: raise AppError("MCP_TOOL_NOT_FOUND", tool=tool)
        try: return mcp_client.call_tool(self._spec(r), tool, self.coerce(args, tools[tool].get("input_schema")), config.mcp_timeout())
        except mcp_client.McpError as e:
            raise AppError("MCP_TOOL_FAILED" if e.code == "MCP_TOOL_FAILED" else "MCP_CONNECT_FAILED", reason=str(e)) from None

    def caller(self, uid: str, org_allowed: bool = True) -> Callable[[str, str, dict], Any]:
        """Port for MCP tool nodes, bound to the resource owner; org servers only if the person running may use them."""
        return lambda sid, tool, args: self.call(uid, sid, tool, args, org_allowed)
