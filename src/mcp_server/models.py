"""
Data models for MCP Server
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class PromptRole(str, Enum):
    """Enum for prompt roles"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class Prompt(BaseModel):
    """Prompt model"""
    id: str = Field(..., description="Unique ID")
    name: str = Field(..., description="Short label")
    role: PromptRole = Field(..., description="Role type")
    content: str = Field(..., description="The actual prompt text")
    tags: List[str] = Field(default_factory=list, description="Optional tags")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last updated timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "prompt_001",
                "name": "Code Review Prompt",
                "role": "system",
                "content": "Review the following code for best practices...",
                "tags": ["code-review", "quality"],
                "updated_at": "2025-10-20T10:00:00"
            }
        }


class PromptCreate(BaseModel):
    """Create prompt request"""
    name: str
    role: PromptRole
    content: str
    tags: Optional[List[str]] = []


class PromptUpdate(BaseModel):
    """Update prompt request"""
    name: Optional[str] = None
    role: Optional[PromptRole] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None


class Resource(BaseModel):
    """Resource model"""
    id: str = Field(..., description="Unique ID")
    name: str = Field(..., description="Resource title")
    description: str = Field(..., description="Summary")
    content: str = Field(..., description="Text, markdown, or code")
    category: str = Field(..., description="Category like 'RabbitMQ', 'Code Conventions'")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last updated timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "resource_001",
                "name": "RabbitMQ Setup Guide",
                "description": "Complete guide for RabbitMQ setup",
                "content": "# RabbitMQ Setup\n...",
                "category": "Messaging",
                "updated_at": "2025-10-20T10:00:00"
            }
        }


class ResourceCreate(BaseModel):
    """Create resource request"""
    name: str
    description: str
    content: str
    category: str


class ResourceUpdate(BaseModel):
    """Update resource request"""
    name: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None


class Tool(BaseModel):
    """Tool model"""
    id: str = Field(..., description="Unique ID")
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Purpose of tool")
    code: str = Field(..., description="Python or shell snippet")
    tags: List[str] = Field(default_factory=list, description="Optional labels")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last updated timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "tool_001",
                "name": "Database Backup",
                "description": "Creates a backup of the database",
                "code": "#!/bin/bash\npg_dump...",
                "tags": ["backup", "database"],
                "updated_at": "2025-10-20T10:00:00"
            }
        }


class ToolCreate(BaseModel):
    """Create tool request"""
    name: str
    description: str
    code: str
    tags: Optional[List[str]] = []


class ToolUpdate(BaseModel):
    """Update tool request"""
    name: Optional[str] = None
    description: Optional[str] = None
    code: Optional[str] = None
    tags: Optional[List[str]] = None


class MCPResponse(BaseModel):
    """Standard MCP response format"""
    success: bool
    data: List[dict]
    count: int

