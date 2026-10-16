"""`{{state.field}}` prompt/URL templating."""
from __future__ import annotations
import json, re
from typing import Any, Dict

VAR_RE = re.compile(r"\{\{\s*state\.([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


def render(template: str, state: Dict[str, Any]) -> str:
    def rep(m):
        v = state.get(m.group(1), "")
        return v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    return VAR_RE.sub(rep, template or "")
