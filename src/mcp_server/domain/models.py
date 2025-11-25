"""
Domain models used across the clean architecture layers.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class PromptRole(str, Enum):
    system = "system"
    user = "user"
    assistant = "assistant"


class TimestampedModel(BaseModel):
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        extra = "forbid"


class Prompt(TimestampedModel):
    id: str
    name: str
    role: PromptRole
    content: str
    tags: List[str] = Field(default_factory=list)


class PromptCreate(BaseModel):
    name: str
    role: PromptRole
    content: str
    tags: List[str] = Field(default_factory=list)


class PromptUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[PromptRole] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None


class Resource(TimestampedModel):
    id: str
    name: str
    description: str
    content: str
    category: str
    tags: List[str] = Field(default_factory=list)


class ResourceCreate(BaseModel):
    name: str
    description: str
    content: str
    category: str
    tags: List[str] = Field(default_factory=list)


class ResourceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None


class Tool(TimestampedModel):
    id: str
    name: str
    description: str
    code: str
    tags: List[str] = Field(default_factory=list)


class ToolCreate(BaseModel):
    name: str
    description: str
    code: str
    tags: List[str] = Field(default_factory=list)


class ToolUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    code: Optional[str] = None
    tags: Optional[List[str]] = None


class MCPResponse(BaseModel):
    success: bool
    data: List[dict]
    count: int


