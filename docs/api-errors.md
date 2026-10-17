# API response envelope and error codes (DEC-0010)

## Envelope (every REST endpoint)

```jsonc
// success
{"success": true, "data": <payload>, "error": null}
// error
{"success": false, "data": null, "error": {"code": "AUTH_INVALID_CREDENTIALS", "message": "Incorrect email or password", "details": <optional>}}
```

- `meta` is reserved for later use (e.g. pagination) and is not sent today.
- `code` is stable UPPER_SNAKE and is the contract. `message` is English and for humans/logs only. Clients translate by `code` and fall back to `message`.
- `details`: 422 → `[{"field": "nodes.0.id", "message": "..."}]`; `WORKFLOW_INVALID` → list of validator messages.
- An expired token returns `AUTH_TOKEN_EXPIRED` **and** the header `X-Auth-Error: expired`.
- Unhandled exceptions → 500 `INTERNAL_ERROR` (logged; no internals in the message).

## Implementation (one place each)

| Concern | Where |
|---|---|
| Code catalog (single source of truth: status + English message template) | `backend/app/core/errors.py` `CATALOG` |
| Raising | `raise AppError("CODE", details=..., **template_params)`; no per-route try/except |
| Success wrapping | `schemas/envelope.py` `EnvelopeResponse` (FastAPI `default_response_class`) |
| Error wrapping | `api/error_handlers.py`: one handler each for AppError, 422, HTTP 404/405, unhandled Exception |
| Frontend unwrap | `frontend/src/lib/api.ts` `api()` |
| Frontend translation | `frontend/src/locales/{en,vi}.json` → `errors.<CODE>`; `lib/i18n.ts` `errorText()` |

`backend/tests/test_api_envelope.py` checks that every catalog code appears in this table and in both locale files.

## WebSocket `/ws/run` error events

```jsonc
{"type": "error", "error": {"code": "NODE_FAILED", "message": "...", "details": [...]}, "errors": ["..."], "node": "classify", ...}
```

`errors` (a list of strings) is kept for the trace UI and stored history. An auth failure still closes with code **4401**. A timeout event carries `status: "timeout"` and code `RUN_TIMEOUT`.

## Code catalog

| Code | HTTP | English message |
|---|---|---|
| `VALIDATION_ERROR` | 422 | Request validation failed |
| `BAD_REQUEST` | 400 | Bad request |
| `NOT_FOUND` | 404 | Resource not found |
| `METHOD_NOT_ALLOWED` | 405 | Method not allowed |
| `PAYLOAD_TOO_LARGE` | 413 | Payload too large |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `AUTH_REQUIRED` | 401 | Authentication required |
| `AUTH_TOKEN_INVALID` | 401 | Invalid token |
| `AUTH_TOKEN_EXPIRED` | 401 | Session expired, please sign in again |
| `AUTH_INVALID_CREDENTIALS` | 401 | Incorrect email or password |
| `AUTH_EMAIL_INVALID` | 400 | Invalid email address |
| `AUTH_EMAIL_TAKEN` | 409 | Email is already registered |
| `AUTH_PASSWORD_TOO_SHORT` | 400 | Password must be at least {min} characters |
| `AUTH_PASSWORD_TOO_LONG` | 400 | Password must be at most {max} characters |
| `AUTH_PASSWORD_WEAK` | 400 | Password must contain both letters and digits |
| `WORKFLOW_NOT_FOUND` | 404 | Workflow not found |
| `WORKFLOW_FORBIDDEN` | 403 | You do not have access to this workflow |
| `WORKFLOW_NAME_REQUIRED` | 400 | Workflow name is required |
| `WORKFLOW_NAME_TOO_LONG` | 400 | Workflow name must be at most {max} characters |
| `WORKFLOW_NAME_TAKEN` | 409 | A workflow with this name already exists |
| `WORKFLOW_TOO_LARGE` | 413 | Workflow is too large (max {max_kb} KB) |
| `WORKFLOW_INVALID` | 400 | Workflow is invalid |
| `RUN_REQUEST_INVALID` | 400 | Run request must be a JSON object |
| `RUN_INPUT_INVALID` | 400 | Run input must be a JSON object |
| `RUN_INPUT_TOO_LARGE` | 413 | Run input is too large (max {max_kb} KB) |
| `RUN_FAILED` | 500 | Run failed |
| `RUN_TIMEOUT` | 408 | Run exceeded the time limit ({seconds}s, STUDIO_RUN_TIMEOUT) |
| `RUN_NOT_FOUND` | 404 | Run not found, already finished or not yours |
| `NODE_FAILED` | 500 | Node failed |
| `CREDENTIAL_NOT_FOUND` | 404 | Credential not found or not yours |
| `CREDENTIAL_PROVIDER_UNSUPPORTED` | 400 | Unsupported provider: {provider} |
| `CREDENTIAL_KEY_REQUIRED` | 400 | API key is required |
| `CREDENTIAL_BASE_URL_INVALID` | 400 | Base URL must start with http:// or https:// |
| `CREDENTIAL_DECRYPT_FAILED` | 500 | Could not decrypt credential (was the secret key changed?) |
| `KB_NOT_FOUND` | 404 | Knowledge base not found or not yours |
| `KB_NAME_REQUIRED` | 400 | Knowledge base name is required |
| `KB_NAME_TOO_LONG` | 400 | Knowledge base name must be at most {max} characters |
| `KB_DOCUMENT_NOT_FOUND` | 404 | Document not found |
| `KB_FILE_REQUIRED` | 400 | Choose a file to upload |
| `KB_FILE_TYPE_UNSUPPORTED` | 400 | Unsupported file type (allowed: {allowed}) |
| `KB_FILE_TOO_LARGE` | 413 | File is too large (max {max_mb} MB) |
| `KB_FILE_UNREADABLE` | 400 | Could not read the file: {reason} |
| `KB_FILE_EMPTY` | 400 | The file contains no text |
| `KB_QUERY_REQUIRED` | 400 | Enter a search query |
| `KB_EMBEDDING_FAILED` | 502 | Embedding failed: {reason} |
| `KB_EMBEDDER_CHANGED` | 409 | The embedding model or key changed since the documents were indexed; re-index the knowledge base |
| `MCP_SERVER_NOT_FOUND` | 404 | MCP server not found |
| `MCP_NAME_REQUIRED` | 400 | MCP server name is required |
| `MCP_NAME_TOO_LONG` | 400 | MCP server name must be at most {max} characters |
| `MCP_TRANSPORT_UNSUPPORTED` | 400 | Unsupported MCP transport: {transport} |
| `MCP_CONFIG_INVALID` | 400 | MCP server setting {field} is missing or invalid |
| `MCP_URL_INVALID` | 400 | The MCP server URL must be a public http(s) URL |
| `MCP_STDIO_DISABLED` | 403 | stdio MCP servers are disabled on this server (STUDIO_MCP_STDIO) |
| `MCP_ADMIN_REQUIRED` | 403 | Only an admin can manage stdio or organization MCP servers |
| `MCP_CONNECT_FAILED` | 502 | Could not talk to the MCP server: {reason} |
| `MCP_TOOL_NOT_FOUND` | 404 | The MCP server has no tool named {tool} |
| `MCP_TOOL_FAILED` | 502 | The MCP tool failed: {reason} |
| `MCP_ARGUMENT_INVALID` | 400 | Argument {name} must be of type {type} |
| `IMPORT_SOURCE_REQUIRED` | 400 | A GitHub URL or a zip file is required |
| `IMPORT_ZIP_TOO_LARGE` | 413 | Zip file is too large (max 50 MB) |
| `IMPORT_INVALID` | 400 | Import failed: {reason} |
| `IMPORT_JOB_NOT_FOUND` | 404 | Import job not found |
| `IMPORT_NOT_READY` | 400 | Import job is not ready or the graph is invalid |
| `AUTH_ACCOUNT_DISABLED` | 403 | This account has been deactivated |
| `PERMISSION_DENIED` | 403 | Your role does not allow this ({permission}) |
| `USER_NOT_FOUND` | 404 | User not found |
| `USER_ROLE_INVALID` | 400 | Role must be one of: {roles} |
| `USER_LAST_ADMIN` | 409 | The studio needs at least one active admin |
| `USER_SELF_CHANGE` | 409 | You cannot change your own role or deactivate your own account |
| `SHARE_USER_NOT_FOUND` | 404 | No active account with that email |
| `SHARE_ROLE_INVALID` | 400 | Share role must be viewer or editor |
| `SHARE_OWNER` | 400 | The owner already has full access |
| `SHARE_NOT_FOUND` | 404 | This workflow is not shared with that user |
| `SLACK_OAUTH_NOT_CONFIGURED` | 503 | Add to Slack is not configured (SLACK_CLIENT_ID / SLACK_CLIENT_SECRET) |
| `SLACK_OAUTH_STATE_INVALID` | 400 | The Slack sign-in link is invalid or expired, please try again |
| `SLACK_OAUTH_FAILED` | 502 | Slack did not complete the installation: {reason} |
| `TEAM_NOT_FOUND` | 404 | Team not found |
| `TEAM_NAME_REQUIRED` | 400 | Team name is required |
| `TEAM_NAME_TAKEN` | 409 | A team with this name already exists |
| `TEAM_MEMBER_NOT_FOUND` | 404 | This user is not a member of the team |
| `TRANSFER_SAME_OWNER` | 400 | This user already owns the workflow |
| `TRANSFER_TARGET_ROLE` | 400 | The new owner must be an editor or an admin |
| `TRANSFER_REBIND_INVALID` | 400 | Node {node}: choose a resource the new owner can use |
| `USER_HAS_WORKFLOWS` | 409 | This user owns {count} workflow(s): choose who takes them over first |
| `USER_DELETE_MODE_INVALID` | 400 | Mode must be anonymize or delete |
| `WORKFLOW_IN_USE` | 409 | {count} workflow(s) use this workflow as a subgraph |
| `ORG_RESOURCE_NOT_ALLOWED` | 403 | Your role may not use organization-wide resources at run time ({kind}) |
| `RUN_NOT_WAITING` | 409 | This run is not waiting for a response |
| `RUN_RESPONSE_INVALID` | 400 | The response must be text (max {max} characters) |
| `TRIGGER_TOKEN_INVALID` | 401 | Missing, invalid or revoked workflow token |
| `TOKEN_NOT_FOUND` | 404 | Token not found |
| `CALLBACK_URL_INVALID` | 400 | callback_url must be a public http(s) URL |
| `VERSION_NOT_FOUND` | 404 | Workflow version not found |
| `RUN_EXPIRED` | 410 | This run waited too long for a response and expired |
| `RATE_LIMITED` | 429 | Too many requests, retry in {retry_after} s |
| `NOTIFICATION_NOT_FOUND` | 404 | Notification not found |
| `DELIVERY_NOT_FOUND` | 404 | Webhook delivery not found |
| `NOTIFICATION_PREFS_INVALID` | 422 | Preferences: in_app and email must be booleans, lang must be en or vi |
| `CHANNEL_KIND_UNSUPPORTED` | 400 | Unsupported approval channel: {kind} |
| `CHANNEL_CONFIG_INVALID` | 400 | Channel setting {field} is missing or invalid |
| `CHANNEL_NOT_FOUND` | 404 | Approval channel not configured |
| `CHANNEL_ADMIN_REQUIRED` | 403 | Only an admin can manage org-wide approval channels |
| `CHANNEL_PUBLIC_URL_REQUIRED` | 400 | Set STUDIO_PUBLIC_URL to the public https URL of the studio first |
| `CHANNEL_SIGNATURE_INVALID` | 401 | Invalid channel request signature |
| `CHANNEL_API_FAILED` | 502 | The {kind} API call failed: {reason} |
| `IDENTITY_INVALID` | 400 | Invalid {kind} user id |
| `IDENTITY_TAKEN` | 409 | This {kind} account is already linked to another user |
| `IDENTITY_NOT_LINKED` | 404 | Link your {kind} account first |
| `IDENTITY_CODE_INVALID` | 400 | Wrong code, {left} attempt(s) left |
| `IDENTITY_CODE_EXPIRED` | 410 | The code expired, request a new one |
| `IDENTITY_CODE_ATTEMPTS` | 429 | Too many wrong codes, request a new one |
| `APPROVAL_TOKEN_INVALID` | 400 | Invalid approval button |
| `APPROVAL_TOKEN_EXPIRED` | 410 | This approval request has expired |
| `APPROVAL_ALREADY_DECIDED` | 409 | This request was already answered |
| `APPROVAL_IDENTITY_UNKNOWN` | 403 | Link and verify your {kind} account in LangGraph Studio (Settings → My accounts) to approve |
| `APPROVAL_FORBIDDEN` | 403 | You are not allowed to approve this run |

Codes used only in WebSocket events (`RUN_*`, `NODE_FAILED`) list their nominal status for reference.
