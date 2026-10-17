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
| `IMPORT_SOURCE_REQUIRED` | 400 | A GitHub URL or a zip file is required |
| `IMPORT_ZIP_TOO_LARGE` | 413 | Zip file is too large (max 50 MB) |
| `IMPORT_INVALID` | 400 | Import failed: {reason} |
| `IMPORT_JOB_NOT_FOUND` | 404 | Import job not found |
| `IMPORT_NOT_READY` | 400 | Import job is not ready or the graph is invalid |
| `RUN_NOT_WAITING` | 409 | This run is not waiting for a response |
| `RUN_RESPONSE_INVALID` | 400 | The response must be text (max {max} characters) |
| `TRIGGER_TOKEN_INVALID` | 401 | Missing, invalid or revoked workflow token |
| `TOKEN_NOT_FOUND` | 404 | Token not found |
| `CALLBACK_URL_INVALID` | 400 | callback_url must be a public http(s) URL |

Codes used only in WebSocket events (`RUN_*`, `NODE_FAILED`) list their nominal status for reference.
