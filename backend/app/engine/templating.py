"""`{{state.field}}` prompt/URL templating."""
from __future__ import annotations
import json, re
from typing import Any, Dict

VAR_RE = re.compile(r"\{\{\s*state\.([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


def render_args(args: Any, state: Dict[str, Any]) -> Any:
    """Render templates inside tool arguments: a string that is exactly one `{{state.x}}` keeps the value's type."""
    if isinstance(args, dict): return {k: render_args(v, state) for k, v in args.items()}
    if isinstance(args, list): return [render_args(v, state) for v in args]
    if isinstance(args, str):
        m = VAR_RE.fullmatch(args.strip())
        return state.get(m.group(1)) if m else render(args, state)
    return args


def render(template: str, state: Dict[str, Any]) -> str:
    def rep(m):
        v = state.get(m.group(1), "")
        return v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    return VAR_RE.sub(rep, template or "")
