"""LLM calls for the LLM node: dispatches to the provider registry (engine/providers.py), deterministic mock otherwise.

Credentials arrive already decrypted from the run's resolver (services.credential_service);
without one, OPENAI_API_KEY from the environment is used, then the mock."""
from __future__ import annotations
import os
from typing import Any, Dict, Optional
from . import providers
from .providers import LLMError, ProviderError  # noqa: F401 (re-exported)
from .usage import estimate_tokens, make_usage


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


def _post(provider: str, url: str, headers: Dict[str, str], body: Dict[str, Any]) -> Dict[str, Any]:
    return providers.request(provider, "POST", url, headers, body)


def call_llm(prompt: str, model: str, cred: Optional[Dict[str, Any]] = None, on_usage=None) -> str:
    """cred: decrypted credential {provider, base_url, api_key, headers}. Without cred falls back to env OPENAI_API_KEY, then mock.
    on_usage(usage): optional callback with the token usage record (engine/usage.make_usage)."""
    report = on_usage or (lambda u: None)
    if cred is None:
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            out = mock_llm(prompt, model)
            report(make_usage("mock", model, estimate_tokens(prompt), estimate_tokens(out), estimated=True))
            return out
        cred = {"provider": "openai", "api_key": key, "base_url": os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")}
    p = providers.get(cred["provider"])
    if p is None: raise LLMError(f"Unsupported provider: {cred['provider']}")
    out, usage = p.invoke(prompt, model, cred)
    report(usage)
    return out


def chat_model(cred: Dict[str, Any], model: str, **kw: Any):
    """LangChain chat model for a decrypted credential (streaming, `bind_tools`)."""
    p = providers.get(cred["provider"])
    if p is None: raise LLMError(f"Unsupported provider: {cred['provider']}")
    return p.chat_model(cred, model or p.default_model, **kw)
