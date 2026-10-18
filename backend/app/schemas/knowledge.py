from typing import Optional
from pydantic import BaseModel


class KnowledgeBaseIn(BaseModel):
    name: str
    description: Optional[str] = None
    model: Optional[str] = None
    credential_id: Optional[str] = None


class SearchIn(BaseModel):
    query: str
    top_k: int = 4
