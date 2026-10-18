"""Workflow naming rules (pure functions)."""
import re
from ..core.config import NAME_MAX
from ..core.errors import AppError


def clean_name(name) -> str:
    n = " ".join(str(name or "").split())
    if not n: raise AppError("WORKFLOW_NAME_REQUIRED")
    if len(n) > NAME_MAX: raise AppError("WORKFLOW_NAME_TOO_LONG", max=NAME_MAX)
    return n


def unique_name(existing: set[str], base: str) -> str:
    """'X' -> 'X (copy)' -> 'X (copy 2)'... unique among `existing`, trimmed to NAME_MAX."""
    if base not in existing: return base
    root = re.sub(r" \(copy(?: \d+)?\)$", "", base)
    def mk(suffix): return f"{root[:NAME_MAX - len(suffix)].rstrip()}{suffix}"
    n, cand = 1, mk(" (copy)")
    while cand in existing: n += 1; cand = mk(f" (copy {n})")
    return cand
