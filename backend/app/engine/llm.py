"""LLM calls: OpenAI-compatible HTTP when OPENAI_API_KEY is set, deterministic mock otherwise.
TASK-0005 (PR #2) ports its provider/credential support here (see docs/backend-architecture.md)."""
from __future__ import annotations
import os
import httpx


def mock_llm(prompt: str, model: str) -> str:
    """Deterministic offline mock. Recognises classification prompts."""
    p = prompt.lower()
    if "classify" in p or "phân loại" in p:
        msg = p.split("message:")[-1] if "message:" in p else p
        if any(k in msg for k in ["order", "đơn", "giao hàng", "ship", "a100", "b200", "c300"]):
            return "order_status"
        if any(k in msg for k in ["refund", "hoàn tiền", "return"]):
            return "refund"
        return "general"
    tail = prompt.strip().splitlines()[-1] if prompt.strip() else ""
    return f"[mock:{model}] Trả lời: {tail[:200]}"


def call_llm(prompt: str, model: str) -> str:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return mock_llm(prompt, model)
    base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    r = httpx.post(f"{base}/chat/completions", headers={"Authorization": f"Bearer {key}"},
                   json={"model": model or "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}]},
                   timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()
