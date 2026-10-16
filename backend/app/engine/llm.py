"""LLM providers: OpenAI(-compatible) and Anthropic over HTTP, deterministic mock otherwise.

Credentials arrive already decrypted from the run's resolver (services.credential_service);
without one, OPENAI_API_KEY from the environment is used, then the mock."""
from __future__ import annotations
import os
from typing import Any, Dict, Optional
import httpx
from .usage import estimate_tokens, make_usage

PROVIDERS = {
    "openai": {"label": "OpenAI / OpenAI-compatible", "default_base_url": "https://api.openai.com/v1"},
    "anthropic": {"label": "Anthropic", "default_base_url": "https://api.anthropic.com"},
}


class LLMError(Exception):
    pass


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


def http_client() -> httpx.Client:
    """Factory for outbound LLM HTTP calls (tests replace this with a MockTransport client)."""
    return httpx.Client(timeout=60)


def _post(provider: str, url: str, headers: Dict[str, str], body: Dict[str, Any]) -> Dict[str, Any]:
    try:
        with http_client() as c:
            r = c.post(url, headers=headers, json=body)
    except httpx.HTTPError as e:
        raise LLMError(f"{provider}: connection failed ({type(e).__name__})") from None
    if r.status_code >= 400:
        try: msg = r.json().get("error", {}).get("message") or r.text
        except Exception: msg = r.text
        raise LLMError(f"{provider}: HTTP {r.status_code}: {str(msg)[:200]}")
    return r.json()


def call_llm(prompt: str, model: str, cred: Optional[Dict[str, Any]] = None, on_usage=None) -> str:
    """cred: decrypted credential {provider, base_url, api_key}. Without cred falls back to env OPENAI_API_KEY, then mock.
    on_usage(usage): optional callback with the token usage record (engine/usage.make_usage)."""
    report = on_usage or (lambda u: None)
    if cred is None:
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            out = mock_llm(prompt, model)
            report(make_usage("mock", model, estimate_tokens(prompt), estimate_tokens(out), estimated=True))
            return out
        cred = {"provider": "openai", "api_key": key, "base_url": os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")}
    provider, key, base = cred["provider"], cred["api_key"], (cred.get("base_url") or "").rstrip("/")
    if provider == "anthropic":
        data = _post("anthropic", f"{base or 'https://api.anthropic.com'}/v1/messages",
                     {"x-api-key": key, "anthropic-version": "2023-06-01"},
                     {"model": model or "claude-3-5-haiku-latest", "max_tokens": 1024, "messages": [{"role": "user", "content": prompt}]})
        try: out = "".join(b.get("text", "") for b in data["content"] if b.get("type") == "text").strip()
        except Exception: raise LLMError("anthropic: invalid response") from None
        u = data.get("usage") or {}
        report(make_usage("anthropic", data.get("model") or model, u.get("input_tokens", 0), u.get("output_tokens", 0)))
        return out
    data = _post("openai", f"{base or 'https://api.openai.com/v1'}/chat/completions", {"Authorization": f"Bearer {key}"},
                 {"model": model or "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}]})
    try: out = data["choices"][0]["message"]["content"].strip()
    except Exception: raise LLMError("openai: invalid response") from None
    u = data.get("usage") or {}
    if u: report(make_usage("openai", data.get("model") or model, u.get("prompt_tokens", 0), u.get("completion_tokens", 0)))
    else: report(make_usage("openai", model, estimate_tokens(prompt), estimate_tokens(out), estimated=True))
    return out
