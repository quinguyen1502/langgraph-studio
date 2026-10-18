from typing import Any, Literal, Optional
from pydantic import BaseModel, Field


class TokenIn(BaseModel):
    name: str = Field("API token", max_length=80)


class TriggerIn(BaseModel):
    input: dict[str, Any] = Field(default_factory=dict)
    mode: Literal["async", "sync"] = "async"
    callback_url: Optional[str] = Field(None, max_length=2000)


class ScheduleIn(BaseModel):  # TASK-0046
    name: str = Field("Schedule", max_length=80)
    cron: str = Field(..., max_length=120)
    timezone: str = Field("UTC", max_length=64)
    input: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class SchedulePatch(BaseModel):
    name: Optional[str] = Field(None, max_length=80)
    cron: Optional[str] = Field(None, max_length=120)
    timezone: Optional[str] = Field(None, max_length=64)
    input: Optional[dict[str, Any]] = None
    enabled: Optional[bool] = None


class SchedulePreview(BaseModel):
    cron: str = Field(..., max_length=120)
    timezone: str = Field("UTC", max_length=64)
