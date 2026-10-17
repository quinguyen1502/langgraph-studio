"""Text embeddings for knowledge bases (TASK-0012): OpenAI(-compatible) `/embeddings`, deterministic mock offline.

Selection mirrors engine/llm: a decrypted credential, else OPENAI_API_KEY from the environment, else the mock.
`embedder_id` names the effective embedder so stored vectors and query vectors are never mixed."""
from __future__ import annotations
import hashlib, math, os, re
from typing import Any, Dict, List, Optional
from .llm import LLMError, _post

DEFAULT_MODEL = "text-embedding-3-small"
MOCK_DIMS = 512
BATCH = 96
_TOKEN = re.compile(r"\w+", re.UNICODE)


STOP = frozenset("a an and are as at be by do does for from how i in is it my of on or our the to was we what when where which who why will with you your "
                 "là và của có cho không được các những một này đó thì với tôi bạn".split())


def _stem(w: str) -> str:
    for suf in ("ing", "ed", "es", "s"):
        if len(w) > len(suf) + 2 and w.endswith(suf): return w[:-len(suf)]
    return w


def mock_embed(text: str, dims: int = MOCK_DIMS) -> List[float]:
    """Feature-hashed bag of stemmed words without stop words, L2-normalised: deterministic, offline, and texts that
    share content words score higher (enough to exercise retrieval end to end; not a semantic model)."""
    v = [0.0] * dims
    for w in _TOKEN.findall(text.lower()):
        if w in STOP: continue
        v[int.from_bytes(hashlib.blake2b(_stem(w).encode(), digest_size=4).digest(), "big") % dims] += 1.0
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def effective(model: str | None, cred: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """The OpenAI-style credential to use, or None for the mock."""
    if cred is not None:
        if cred.get("provider") != "openai": raise LLMError(f"{cred.get('provider')}: embeddings need an OpenAI-compatible credential")
        return cred
    key = os.environ.get("OPENAI_API_KEY")
    return {"provider": "openai", "api_key": key, "base_url": os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")} if key else None


def embedder_id(model: str | None, cred: Optional[Dict[str, Any]]) -> str:
    return f"openai:{model or DEFAULT_MODEL}" if effective(model, cred) else f"mock:{MOCK_DIMS}"


def embed(texts: List[str], model: str | None = None, cred: Optional[Dict[str, Any]] = None) -> List[List[float]]:
    c = effective(model, cred)
    if c is None: return [mock_embed(t) for t in texts]
    base = (c.get("base_url") or "https://api.openai.com/v1").rstrip("/")
    out: List[List[float]] = []
    for i in range(0, len(texts), BATCH):
        data = _post("openai", f"{base}/embeddings", {"Authorization": f"Bearer {c['api_key']}"},
                     {"model": model or DEFAULT_MODEL, "input": texts[i:i + BATCH]})
        try: out += [d["embedding"] for d in sorted(data["data"], key=lambda d: d["index"])]
        except Exception: raise LLMError("openai: invalid embeddings response") from None
    return out


def cosine(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0
