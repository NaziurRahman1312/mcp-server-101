"""
Resource service with FAISS synchronization.
"""
from __future__ import annotations

from typing import Iterable

from mcp_server.domain import models
from mcp_server.domain.repositories import ResourceRepository
from mcp_server.infrastructure.vector.faiss_store import FaissStore


class ResourceService:
    def __init__(self, repository: ResourceRepository, vector_store: FaissStore):
        self.repository = repository
        self.vector_store = vector_store

    def list_resources(self) -> Iterable[models.Resource]:
        return self.repository.list()

    def get_resource(self, resource_id: str) -> models.Resource | None:
        return self.repository.get(resource_id)

    def create_resource(self, payload: models.ResourceCreate) -> models.Resource:
        resource = self.repository.create(payload)
        self.vector_store.add_or_update("resource", resource.id, self._vector_text(resource))
        return resource

    def update_resource(self, resource_id: str, payload: models.ResourceUpdate) -> models.Resource | None:
        resource = self.repository.update(resource_id, payload)
        if resource:
            self.vector_store.add_or_update("resource", resource.id, self._vector_text(resource))
        return resource

    def delete_resource(self, resource_id: str) -> bool:
        deleted = self.repository.delete(resource_id)
        if deleted:
            self.vector_store.delete("resource", resource_id)
        return deleted

    @staticmethod
    def _vector_text(resource: models.Resource) -> str:
        return "\n".join(filter(None, [resource.name, resource.description, resource.content, ",".join(resource.tags)]))


