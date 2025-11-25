"""
Tool service with FAISS synchronization.
"""
from __future__ import annotations

from typing import Iterable

from mcp_server.domain import models
from mcp_server.domain.repositories import ToolRepository
from mcp_server.infrastructure.vector.faiss_store import FaissStore


class ToolService:
    def __init__(self, repository: ToolRepository, vector_store: FaissStore):
        self.repository = repository
        self.vector_store = vector_store

    def list_tools(self) -> Iterable[models.Tool]:
        return self.repository.list()

    def get_tool(self, tool_id: str) -> models.Tool | None:
        return self.repository.get(tool_id)

    def create_tool(self, payload: models.ToolCreate) -> models.Tool:
        tool = self.repository.create(payload)
        self.vector_store.add_or_update("tool", tool.id, self._vector_text(tool))
        return tool

    def update_tool(self, tool_id: str, payload: models.ToolUpdate) -> models.Tool | None:
        tool = self.repository.update(tool_id, payload)
        if tool:
            self.vector_store.add_or_update("tool", tool.id, self._vector_text(tool))
        return tool

    def delete_tool(self, tool_id: str) -> bool:
        deleted = self.repository.delete(tool_id)
        if deleted:
            self.vector_store.delete("tool", tool_id)
        return deleted

    @staticmethod
    def _vector_text(tool: models.Tool) -> str:
        return "\n".join(filter(None, [tool.name, tool.description, tool.code, ",".join(tool.tags)]))


