"""Error-code catalog (single source of truth) and the one application error type.

Services/engine raise `AppError("CODE", **params)`; `app.api.error_handlers` turns it into the
error envelope. Codes are stable UPPER_SNAKE strings; messages are English templates.
The frontend translates by code (`frontend/src/locales/*.json` → `errors.<CODE>`), falling back to `message`.
"""
from typing import Any

# code: (HTTP status, English message template)
CATALOG: dict[str, tuple[int, str]] = {
    # generic / transport
    "VALIDATION_ERROR": (422, "Request validation failed"),
    "BAD_REQUEST": (400, "Bad request"),
    "NOT_FOUND": (404, "Resource not found"),
    "METHOD_NOT_ALLOWED": (405, "Method not allowed"),
    "PAYLOAD_TOO_LARGE": (413, "Payload too large"),
    "INTERNAL_ERROR": (500, "Internal server error"),
    # auth
    "AUTH_REQUIRED": (401, "Authentication required"),
    "AUTH_TOKEN_INVALID": (401, "Invalid token"),
    "AUTH_TOKEN_EXPIRED": (401, "Session expired, please sign in again"),
    "AUTH_INVALID_CREDENTIALS": (401, "Incorrect email or password"),
    "AUTH_EMAIL_INVALID": (400, "Invalid email address"),
    "AUTH_EMAIL_TAKEN": (409, "Email is already registered"),
    "AUTH_PASSWORD_TOO_SHORT": (400, "Password must be at least {min} characters"),
    "AUTH_PASSWORD_TOO_LONG": (400, "Password must be at most {max} characters"),
    "AUTH_PASSWORD_WEAK": (400, "Password must contain both letters and digits"),
    # workflows
    "WORKFLOW_NOT_FOUND": (404, "Workflow not found"),
    "WORKFLOW_FORBIDDEN": (403, "You do not have access to this workflow"),
    "WORKFLOW_NAME_REQUIRED": (400, "Workflow name is required"),
    "WORKFLOW_NAME_TOO_LONG": (400, "Workflow name must be at most {max} characters"),
    "WORKFLOW_NAME_TAKEN": (409, "A workflow with this name already exists"),
    "WORKFLOW_TOO_LARGE": (413, "Workflow is too large (max {max_kb} KB)"),
    "WORKFLOW_INVALID": (400, "Workflow is invalid"),
    # runs (WebSocket events)
    "RUN_REQUEST_INVALID": (400, "Run request must be a JSON object"),
    "RUN_INPUT_INVALID": (400, "Run input must be a JSON object"),
    "RUN_INPUT_TOO_LARGE": (413, "Run input is too large (max {max_kb} KB)"),
    "RUN_FAILED": (500, "Run failed"),
    "RUN_TIMEOUT": (408, "Run exceeded the time limit ({seconds}s, STUDIO_RUN_TIMEOUT)"),
    "RUN_NOT_FOUND": (404, "Run not found, already finished or not yours"),
    "RUN_NOT_WAITING": (409, "This run is not waiting for a response"),
    "RUN_RESPONSE_INVALID": (400, "The response must be text (max {max} characters)"),
    "TRIGGER_TOKEN_INVALID": (401, "Missing, invalid or revoked workflow token"),
    "TOKEN_NOT_FOUND": (404, "Token not found"),
    "VERSION_NOT_FOUND": (404, "Workflow version not found"),
    "CALLBACK_URL_INVALID": (400, "callback_url must be a public http(s) URL"),
    "NODE_FAILED": (500, "Node failed"),
    # credentials
    "CREDENTIAL_NOT_FOUND": (404, "Credential not found or not yours"),
    "CREDENTIAL_PROVIDER_UNSUPPORTED": (400, "Unsupported provider: {provider}"),
    "CREDENTIAL_KEY_REQUIRED": (400, "API key is required"),
    "CREDENTIAL_BASE_URL_INVALID": (400, "Base URL must start with http:// or https://"),
    "CREDENTIAL_DECRYPT_FAILED": (500, "Could not decrypt credential (was the secret key changed?)"),
    # repo import
    "IMPORT_SOURCE_REQUIRED": (400, "A GitHub URL or a zip file is required"),
    "IMPORT_ZIP_TOO_LARGE": (413, "Zip file is too large (max 50 MB)"),
    "IMPORT_INVALID": (400, "Import failed: {reason}"),
    "IMPORT_JOB_NOT_FOUND": (404, "Import job not found"),
    "IMPORT_NOT_READY": (400, "Import job is not ready or the graph is invalid"),
}


class AppError(Exception):
    def __init__(self, code: str, details: Any = None, headers: dict | None = None, **params):
        self.status, template = CATALOG[code]
        # template params double as `details` so clients can interpolate their own translation
        self.code, self.details, self.headers = code, details if details is not None else (params or None), headers or {}
        self.message = template.format(**params)
        super().__init__(self.message)

    def to_dict(self) -> dict:
        d = {"code": self.code, "message": self.message}
        if self.details is not None: d["details"] = self.details
        return d
