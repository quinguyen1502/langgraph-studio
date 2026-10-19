"""Run-time ports: services a node may call, bound to the run's user by the service layer (TASK-0012/0013).

The engine only sees these callables, never repositories or HTTP clients of other features, so node executors stay
testable with plain functions."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

Retrieve = Callable[[str, str, int], List[Dict[str, Any]]]   # (knowledge_base_id, query, top_k) -> chunks
McpCall = Callable[[str, str, Dict[str, Any]], Any]          # (server_id, tool, arguments) -> result
EmailQuota = Callable[[int], None]                           # (recipients) -> None, raises EMAIL_RATE_LIMITED (TASK-0051)
Cancelled = Callable[[], bool]                               # True once the run was cancelled or timed out (TASK-0053)
CodeAudit = Callable[[], None]                               # records that Code nodes ran without isolation (TASK-0056)


@dataclass
class Ports:
    retrieve: Optional[Retrieve] = None
    mcp_call: Optional[McpCall] = None
    email_quota: Optional[EmailQuota] = None
    cancelled: Optional[Cancelled] = None
    code_audit: Optional[CodeAudit] = None
