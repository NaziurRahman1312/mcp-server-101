"""
Transport-layer schemas for FastAPI responses.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Union

from pydantic import BaseModel

from mcp_server.domain import models as domain_models


class PromptResponse(BaseModel):
    id: str
    name: str
    role: domain_models.PromptRole
    content: str
    tags: List[str]
    updated_at: datetime

    @classmethod
    def from_domain(cls, prompt: domain_models.Prompt) -> "PromptResponse":
        return cls(**prompt.model_dump())


class ResourceResponse(BaseModel):
    id: str
    name: str
    description: str
    content: str
    category: str
    tags: List[str]
    updated_at: datetime

    @classmethod
    def from_domain(cls, resource: domain_models.Resource) -> "ResourceResponse":
        return cls(**resource.model_dump())


class ToolResponse(BaseModel):
    id: str
    name: str
    description: str
    code: str
    tags: List[str]
    updated_at: datetime

    @classmethod
    def from_domain(cls, tool: domain_models.Tool) -> "ToolResponse":
        return cls(**tool.model_dump())


class SearchResultResponse(BaseModel):
    id: str
    type: Literal["prompt", "resource", "tool"]
    score: float
    payload: Union[PromptResponse, ResourceResponse, ToolResponse]


