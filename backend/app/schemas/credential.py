from typing import Optional
from pydantic import BaseModel


class CredentialIn(BaseModel):
    name: str
    provider: str
    api_key: str
    base_url: Optional[str] = None
