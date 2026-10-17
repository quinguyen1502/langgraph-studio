from typing import Any, Literal, Optional
from pydantic import BaseModel, Field


class TokenIn(BaseModel):
    name: str = Field("API token", max_length=80)


class TriggerIn(BaseModel):
    input: dict[str, Any] = Field(default_factory=dict)
    mode: Literal["async", "sync"] = "async"
    callback_url: Optional[str] = Field(None, max_length=2000)
