"""Domain errors raised by services, and their mapping to HTTP responses.

Pure Python (no FastAPI import); `app.api.error_handlers` maps them to HTTP status codes.
"""


class DomainError(Exception):
    status = 400
    def __init__(self, message: str, headers: dict | None = None):
        super().__init__(message); self.message = message; self.headers = headers or {}

class BadRequest(DomainError): status = 400
class Unauthorized(DomainError): status = 401
class Forbidden(DomainError): status = 403
class NotFound(DomainError): status = 404
class Conflict(DomainError): status = 409
class TooLarge(DomainError): status = 413
