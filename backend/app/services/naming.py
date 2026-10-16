"""Workflow naming rules (pure functions)."""
import re
from ..core.config import NAME_MAX
from ..core.errors import BadRequest


def clean_name(name) -> str:
    n = " ".join(str(name or "").split())
    if not n: raise BadRequest("Tên workflow không được để trống")
    if len(n) > NAME_MAX: raise BadRequest(f"Tên workflow tối đa {NAME_MAX} ký tự")
    return n


def unique_name(existing: set[str], base: str) -> str:
    """'X' -> 'X (copy)' -> 'X (copy 2)'... unique among `existing`, trimmed to NAME_MAX."""
    if base not in existing: return base
    root = re.sub(r" \(copy(?: \d+)?\)$", "", base)
    def mk(suffix): return f"{root[:NAME_MAX - len(suffix)].rstrip()}{suffix}"
    n, cand = 1, mk(" (copy)")
    while cand in existing: n += 1; cand = mk(f" (copy {n})")
    return cand
