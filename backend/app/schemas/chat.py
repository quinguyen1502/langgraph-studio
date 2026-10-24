"""Web chat (TASK-0084): the workflow's Chat settings. Unset fields keep their value."""
from typing import Optional
from pydantic import BaseModel


class ChatSettingsIn(BaseModel):
    enabled: Optional[bool] = None
    access: Optional[str] = None          # studio (phase 1); anonymous | signed_in are reserved for the published page
    input_field: Optional[str] = None
    reply_field: Optional[str] = None
    messages_field: Optional[str] = None  # a list field that gets the history, or "" for none
    max_turns: Optional[int] = None
    steps: Optional[str] = None           # none | labels | full: what a visitor sees (builders always see full)
    retention_days: Optional[int] = None
