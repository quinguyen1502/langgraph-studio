from typing import Dict, Optional
from pydantic import BaseModel


class CredentialIn(BaseModel):
    name: str
    provider: str
    api_key: str = ""                          # optional for local providers (Ollama, LM Studio, ...)
    base_url: Optional[str] = None
    headers: Optional[Dict[str, str]] = None   # provider-specific extra headers (OpenRouter: HTTP-Referer, X-Title)


class ProviderProbeIn(BaseModel):
    """Unsaved connection settings for 'Test connection' / model list before the credential is created."""
    api_key: str = ""
    base_url: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    credential_id: Optional[str] = None  # editing: test with this saved credential's key when none is typed


class CredentialUpdate(BaseModel):
    """Edit in place (TASK-0030). The provider is fixed; `api_key` omitted/empty keeps the stored secret,
    `clear_key` removes it (providers where a key is optional)."""
    name: str
    base_url: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    api_key: Optional[str] = None
    clear_key: bool = False


class EmbeddingTestIn(BaseModel):
    model: Optional[str] = None
