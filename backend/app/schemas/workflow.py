"""Workflow DTOs. `extra="allow"` keeps unknown keys (e.g. node `kind`, imported `source`) round-tripping."""
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class NodeIn(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str = Field(min_length=1, max_length=64)
    type: str = Field(min_length=1, max_length=32)
    position: Optional[dict] = None
    data: dict = Field(default_factory=dict)


class EdgeIn(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str = Field(min_length=1, max_length=64)
    source: str = Field(min_length=1)
    target: str = Field(min_length=1)
    label: Optional[str] = None


class FieldIn(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str = Field(min_length=1, max_length=64)
    type: str = "string"


class WorkflowIn(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: Optional[str] = None
    name: Optional[str] = None
    state: list[FieldIn] = Field(default_factory=list, max_length=200)
    nodes: list[NodeIn] = Field(default_factory=list, max_length=500)
    edges: list[EdgeIn] = Field(default_factory=list, max_length=2000)

    def as_dict(self) -> dict:
        return self.model_dump(exclude_none=True)


class Rename(BaseModel):
    name: str


class WorkflowSummary(BaseModel):
    id: str
    name: Optional[str]
    updated: Optional[float]
    node_count: int
    last_run_status: Optional[str]
    last_run_at: Optional[float]
