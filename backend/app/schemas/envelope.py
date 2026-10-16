"""The one response envelope for every REST endpoint (DEC-0010).

success: {"success": true,  "data": <payload>, "error": null}
error:   {"success": false, "data": null, "error": {"code", "message", "details"?}}
"""
from typing import Any
from fastapi.responses import JSONResponse


def ok(data: Any) -> dict:
    return {"success": True, "data": data, "error": None}


def fail(error: dict) -> dict:
    return {"success": False, "data": None, "error": error}


class EnvelopeResponse(JSONResponse):
    """Default response class: wraps whatever a route returns in the success envelope."""
    def render(self, content: Any) -> bytes:
        return super().render(content if isinstance(content, dict) and "success" in content and "error" in content else ok(content))
