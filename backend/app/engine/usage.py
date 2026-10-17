"""LLM token usage and cost (TASK-0010). One place for the price table and the usage record shape."""
from __future__ import annotations
from typing import Any, Callable, Dict, Optional

# USD per 1M tokens (input, output). Unknown models get cost None (shown as "-").
PRICES: Dict[str, tuple[float, float]] = {
    "gpt-4o-mini": (0.15, 0.60), "gpt-4o": (2.50, 10.00), "gpt-4.1-mini": (0.40, 1.60), "gpt-4.1": (2.00, 8.00),
    "claude-3-5-haiku": (0.80, 4.00), "claude-3-5-sonnet": (3.00, 15.00), "claude-3-7-sonnet": (3.00, 15.00),
}

UsageSink = Callable[[str, Dict[str, Any]], None]  # (node_id, usage) -> None


def price_for(model: str) -> Optional[tuple[float, float]]:
    m = (model or "").lower()
    for k in sorted(PRICES, key=len, reverse=True):  # longest prefix wins (gpt-4o-mini before gpt-4o)
        if m.startswith(k): return PRICES[k]
    return None


def make_usage(provider: str, model: str, tokens_in: int, tokens_out: int, estimated: bool = False) -> Dict[str, Any]:
    """Usage record attached to `node_finished` events. Mock runs are estimated and always cost 0."""
    p = None if provider == "mock" else price_for(model)
    cost = 0.0 if provider == "mock" else (round((tokens_in * p[0] + tokens_out * p[1]) / 1e6, 8) if p else None)
    return {"provider": provider, "model": model, "tokens_in": int(tokens_in), "tokens_out": int(tokens_out),
            "tokens": int(tokens_in) + int(tokens_out), "cost_usd": cost, "estimated": estimated}


def estimate_tokens(text: str) -> int:
    return max(1, (len(text or "") + 3) // 4)  # ~4 chars per token; good enough for offline mock runs


def merge(a: Optional[Dict[str, Any]], b: Dict[str, Any]) -> Dict[str, Any]:
    """Sum two usage records (a node may call the LLM more than once in future node types)."""
    if not a: return dict(b)
    out = dict(a)
    for k in ("tokens_in", "tokens_out", "tokens"): out[k] = a[k] + b[k]
    out["cost_usd"] = None if a["cost_usd"] is None or b["cost_usd"] is None else round(a["cost_usd"] + b["cost_usd"], 8)
    out["estimated"] = a["estimated"] or b["estimated"]
    return out
