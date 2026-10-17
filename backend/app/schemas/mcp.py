from typing import Dict, List, Optional
from pydantic import BaseModel


class McpServerIn(BaseModel):
    name: str
    transport: str = "http"          # fixed after creation
    scope: str = "user"              # fixed after creation
    command: Optional[str] = None
    args: Optional[List[str]] = None
    url: Optional[str] = None
    secrets: Optional[Dict[str, Optional[str]]] = None  # null value = keep the stored one
