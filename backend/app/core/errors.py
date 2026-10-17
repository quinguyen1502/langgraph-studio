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
    # templates (TASK-0025)
    "TEMPLATE_NOT_FOUND": (404, "Template not found"),
    "TEMPLATE_READ_ONLY": (403, "This template cannot be deleted"),
    "TEMPLATE_INVALID": (400, "Not a valid template file"),
    "TEMPLATE_NAME_REQUIRED": (400, "Template name is required"),
    "TEMPLATE_SCOPE_FORBIDDEN": (403, "Only administrators can share templates with the whole organisation"),
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
    "RUN_EXPIRED": (410, "This run waited too long for a response and expired"),
    "RATE_LIMITED": (429, "Too many requests, retry in {retry_after} s"),
    "NOTIFICATION_NOT_FOUND": (404, "Notification not found"),
    "DELIVERY_NOT_FOUND": (404, "Webhook delivery not found"),
    "NOTIFICATION_PREFS_INVALID": (422, "Preferences: in_app and email must be booleans, lang must be en or vi"),
    "VERSION_NOT_FOUND": (404, "Workflow version not found"),
    "CALLBACK_URL_INVALID": (400, "callback_url must be a public http(s) URL"),
    "NODE_FAILED": (500, "Node failed"),
    # approval channels (TASK-0022)
    "CHANNEL_KIND_UNSUPPORTED": (400, "Unsupported approval channel: {kind}"),
    "CHANNEL_CONFIG_INVALID": (400, "Channel setting {field} is missing or invalid"),
    "CHANNEL_NOT_FOUND": (404, "Approval channel not configured"),
    "CHANNEL_ADMIN_REQUIRED": (403, "Only an admin can manage org-wide approval channels"),
    "CHANNEL_PUBLIC_URL_REQUIRED": (400, "Set STUDIO_PUBLIC_URL to the public https URL of the studio first"),
    "CHANNEL_SIGNATURE_INVALID": (401, "Invalid channel request signature"),
    "CHANNEL_API_FAILED": (502, "The {kind} API call failed: {reason}"),
    "IDENTITY_INVALID": (400, "Invalid {kind} user id"),
    "IDENTITY_TAKEN": (409, "This {kind} account is already linked to another user"),
    "APPROVAL_TOKEN_INVALID": (400, "Invalid approval button"),
    "APPROVAL_TOKEN_EXPIRED": (410, "This approval request has expired"),
    "APPROVAL_ALREADY_DECIDED": (409, "This request was already answered"),
    "APPROVAL_IDENTITY_UNKNOWN": (403, "Link and verify your {kind} account in LangGraph Studio (Settings → My accounts) to approve"),
    "IDENTITY_NOT_LINKED": (404, "Link your {kind} account first"),
    "IDENTITY_CODE_INVALID": (400, "Wrong code, {left} attempt(s) left"),
    "IDENTITY_CODE_EXPIRED": (410, "The code expired, request a new one"),
    "IDENTITY_CODE_ATTEMPTS": (429, "Too many wrong codes, request a new one"),
    "APPROVAL_FORBIDDEN": (403, "You are not allowed to approve this run"),
    # credentials
    "CREDENTIAL_NOT_FOUND": (404, "Credential not found or not yours"),
    "CREDENTIAL_PROVIDER_UNSUPPORTED": (400, "Unsupported provider: {provider}"),
    "CREDENTIAL_KEY_REQUIRED": (400, "API key is required"),
    "CREDENTIAL_BASE_URL_INVALID": (400, "Base URL must start with http:// or https://"),
    "CREDENTIAL_DECRYPT_FAILED": (500, "Could not decrypt credential (was the secret key changed?)"),
    # knowledge bases (TASK-0012)
    "KB_NOT_FOUND": (404, "Knowledge base not found or not yours"),
    "KB_NAME_REQUIRED": (400, "Knowledge base name is required"),
    "KB_NAME_TOO_LONG": (400, "Knowledge base name must be at most {max} characters"),
    "KB_DOCUMENT_NOT_FOUND": (404, "Document not found"),
    "KB_FILE_REQUIRED": (400, "Choose a file to upload"),
    "KB_FILE_TYPE_UNSUPPORTED": (400, "Unsupported file type (allowed: {allowed})"),
    "KB_FILE_TOO_LARGE": (413, "File is too large (max {max_mb} MB)"),
    "KB_FILE_UNREADABLE": (400, "Could not read the file: {reason}"),
    "KB_FILE_EMPTY": (400, "The file contains no text"),
    "KB_QUERY_REQUIRED": (400, "Enter a search query"),
    "KB_EMBEDDING_FAILED": (502, "Embedding failed: {reason}"),
    "KB_EMBEDDER_CHANGED": (409, "The embedding model or key changed since the documents were indexed; re-index the knowledge base"),
    # MCP servers (TASK-0013)
    "MCP_SERVER_NOT_FOUND": (404, "MCP server not found"),
    "MCP_NAME_REQUIRED": (400, "MCP server name is required"),
    "MCP_NAME_TOO_LONG": (400, "MCP server name must be at most {max} characters"),
    "MCP_TRANSPORT_UNSUPPORTED": (400, "Unsupported MCP transport: {transport}"),
    "MCP_CONFIG_INVALID": (400, "MCP server setting {field} is missing or invalid"),
    "MCP_URL_INVALID": (400, "The MCP server URL must be a public http(s) URL"),
    "MCP_STDIO_DISABLED": (403, "stdio MCP servers are disabled on this server (STUDIO_MCP_STDIO)"),
    "MCP_ADMIN_REQUIRED": (403, "Only an admin can manage stdio or organization MCP servers"),
    "MCP_CONNECT_FAILED": (502, "Could not talk to the MCP server: {reason}"),
    "MCP_TOOL_NOT_FOUND": (404, "The MCP server has no tool named {tool}"),
    "MCP_TOOL_FAILED": (502, "The MCP tool failed: {reason}"),
    "MCP_ARGUMENT_INVALID": (400, "Argument {name} must be of type {type}"),
    # repo import
    "IMPORT_SOURCE_REQUIRED": (400, "A GitHub URL or a zip file is required"),
    "IMPORT_ZIP_TOO_LARGE": (413, "Zip file is too large (max 50 MB)"),
    "IMPORT_INVALID": (400, "Import failed: {reason}"),
    "IMPORT_JOB_NOT_FOUND": (404, "Import job not found"),
    "IMPORT_NOT_READY": (400, "Import job is not ready or the graph is invalid"),
    # RBAC and sharing (TASK-0014)
    "AUTH_ACCOUNT_DISABLED": (403, "This account has been deactivated"),
    "PERMISSION_DENIED": (403, "Your role does not allow this ({permission})"),
    "USER_NOT_FOUND": (404, "User not found"),
    "USER_ROLE_INVALID": (400, "Role must be one of: {roles}"),
    "USER_LAST_ADMIN": (409, "The studio needs at least one active admin"),
    "USER_SELF_CHANGE": (409, "You cannot change your own role or deactivate your own account"),
    "SHARE_USER_NOT_FOUND": (404, "No active account with that email"),
    "SHARE_ROLE_INVALID": (400, "Share role must be viewer or editor"),
    "SHARE_OWNER": (400, "The owner already has full access"),
    "SHARE_NOT_FOUND": (404, "This workflow is not shared with that user"),
    # Slack app distribution (TASK-0014)
    "SLACK_OAUTH_NOT_CONFIGURED": (503, "Add to Slack is not configured (SLACK_CLIENT_ID / SLACK_CLIENT_SECRET)"),
    "SLACK_OAUTH_STATE_INVALID": (400, "The Slack sign-in link is invalid or expired, please try again"),
    "SLACK_OAUTH_FAILED": (502, "Slack did not complete the installation: {reason}"),
    # Phase 3 hardening (TASK-0029)
    "TEAM_NOT_FOUND": (404, "Team not found"),
    "TEAM_NAME_REQUIRED": (400, "Team name is required"),
    "TEAM_NAME_TAKEN": (409, "A team with this name already exists"),
    "TEAM_MEMBER_NOT_FOUND": (404, "This user is not a member of the team"),
    "TRANSFER_SAME_OWNER": (400, "This user already owns the workflow"),
    "TRANSFER_TARGET_ROLE": (400, "The new owner must be an editor or an admin"),
    "TRANSFER_REBIND_INVALID": (400, "Node {node}: choose a resource the new owner can use"),
    "USER_HAS_WORKFLOWS": (409, "This user owns {count} workflow(s): choose who takes them over first"),
    "USER_DELETE_MODE_INVALID": (400, "Mode must be anonymize or delete"),
    "WORKFLOW_IN_USE": (409, "{count} workflow(s) use this workflow as a subgraph"),
    "ORG_RESOURCE_NOT_ALLOWED": (403, "Your role may not use organization-wide resources at run time ({kind})"),
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
