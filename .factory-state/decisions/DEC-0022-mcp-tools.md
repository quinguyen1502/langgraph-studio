# Decision

## Metadata

- Decision ID: DEC-0022
- Status: Accepted (implementation in review)
- Date: 2026-10-17
- Related: TASK-0013, REQ-0011, DEC-0019 (scopes of approval channels), ARCH-0001

## Context

REQ-0011: Tool nodes should call tools exposed by configured MCP servers. The open question was which servers to support first. The owner decided (2026-10-17): a generic registry for stdio and HTTP servers with no bundled servers, tool discovery, and an MCP tool node, with secure handling of environment variables and secrets plus sandbox notes.

## Decisions

### Client: our own, small, specification-based
- `engine/mcp_client.py` implements the three calls we need (`initialize` + `notifications/initialized`, `tools/list` with bounded pagination, `tools/call`) over JSON-RPC 2.0. Transports are stdio (newline-delimited) and Streamable HTTP (JSON or SSE responses, `Mcp-Session-Id`, `MCP-Protocol-Version: 2025-06-18`, DELETE on close).
- Why not the MCP Python SDK: the client side is about 200 lines, and owning it keeps the process sandbox and the outbound HTTP policy under our control. The SDK (2.x) also pulls in a second HTTP stack and newer Starlette. The SDK is used only in an optional interop test (`test_mcp.py::test_interop_with_the_official_sdk_server`, skipped when it is not installed), which runs our client against an SDK-built server.
- One short session per call (discovery or a node run). This is simpler and stateless across API replicas; the cost is a process start per stdio call.
- Results: `structuredContent` if present, else the text content (JSON-decoded when it is JSON), else the raw content list. `isError` raises `MCP_TOOL_FAILED`; transport and protocol problems raise `MCP_CONNECT_FAILED`. Both appear as node error events.

### Registry and permissions
- Table `mcp_servers` (migration `0020_mcp_servers`). The scopes are the same as approval channels: `user` (owner only) and `org` (managed by admins, usable by everyone). Transport and scope are fixed after creation.
- stdio servers start a process on the API/worker host. They need `STUDIO_MCP_STDIO=1` (default off) and an admin. Turning the flag off also stops existing stdio servers (`MCP_STDIO_DISABLED`).
- HTTP servers: any user (personal) or an admin (org). The URL must resolve to public addresses unless `STUDIO_MCP_ALLOW_PRIVATE=1`. Each request connects to the IP validated just before (the pinning helper shared with webhooks, `services/webhooks.public_address`), so a DNS change cannot redirect calls to internal services. Redirects are not followed.
- Admin today means `users.is_admin` (demo user in dev, `STUDIO_ADMIN_EMAILS`). TASK-0014 moves it to RBAC permissions (`org.manage`, DEC-0023).

### Secrets
- One field `secrets` per server: environment variables for stdio, HTTP headers for HTTP (e.g. `Authorization`). They are stored as one Fernet token (the same key as credentials), and only names with masked values are returned. In an update, a `null` value keeps the stored value and names not listed are removed. Changing the configuration clears the cached tools.

### Sandbox notes (stdio)
- The process environment is only `PATH`, `LANG=C.UTF-8`, `HOME`, and the server's declared variables. The studio's own environment (`JWT_SECRET`, `DATABASE_URL`, `STUDIO_SECRET_KEY`, provider keys …) is **not** inherited; a test checks this.
- The working directory and `HOME` are a fresh empty temp directory, removed afterwards.
- Own process group; on timeout or close the whole group is killed. `STUDIO_MCP_TIMEOUT` (default 30 s) applies to each response. stderr is kept only as a 2 KB tail for error messages, which are redacted like other node errors.
- There is no further isolation: the process runs as the API user with its file system and network access. In Compose that means inside the `api`/`worker` container, which is the intended boundary. For untrusted servers, prefer HTTP servers in their own container (sidecar + `STUDIO_MCP_ALLOW_PRIVATE=1`) or keep `STUDIO_MCP_STDIO=0`. The UI shows this note in Settings → MCP servers.

### MCP tool node
- `type: mcp`, `data`: `server_id`, `tool`, `arguments` (object), `output_field`. String arguments are templates: exactly `{{state.x}}` passes the value with its type, otherwise it is text. Before the call, string values are converted to the type declared in the tool's input schema (integer, number, boolean, object/array as JSON); empty optional values are dropped.
- The engine calls the service through `Ports.mcp_call` (introduced in TASK-0012), bound to the run's user, so another user's personal server is `MCP_SERVER_NOT_FOUND`. A tool missing from the cached list triggers one fresh discovery before `MCP_TOOL_NOT_FOUND`.
- A separate node type rather than a third Tool mode: different settings (server/tool/schema-driven arguments) and a distinct colour token `--node-mcp`.

## Consequences
- No bundled servers. Operators add their own: HTTP endpoints, or stdio commands when they enable them.
- Only tools; resources, prompts, sampling and elicitation are out of scope (server requests are answered "not supported").
