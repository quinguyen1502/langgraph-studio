from typing import Optional
from pydantic import BaseModel, Field


class UserUpdate(BaseModel):
    role: Optional[str] = Field(None, max_length=20)
    active: Optional[bool] = None


class ShareIn(BaseModel):
    email: str = Field(..., min_length=3, max_length=254)
    role: str = Field("viewer", max_length=20)
