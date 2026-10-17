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
