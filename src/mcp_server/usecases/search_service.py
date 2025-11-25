"""
Semantic search orchestrator combining FAISS and repositories.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal

from mcp_server.domain import models
from mcp_server.domain.repositories import PromptRepository, ResourceRepository, ToolRepository
from mcp_server.infrastructure.vector.faiss_store import FaissStore

SearchTarget = Literal["resource", "tool", "prompt"]


@dataclass
class SearchResult:
    id: str
    type: SearchTarget
    score: float
    payload: models.Resource | models.Tool | models.Prompt


class SearchService:
    def __init__(
        self,
        prompts: PromptRepository,
        resources: ResourceRepository,
        tools: ToolRepository,
        vector_store: FaissStore,
    ) -> None:
        self.prompts = prompts
        self.resources = resources
        self.tools = tools
        self.vector_store = vector_store

    def search(self, query: str, target: SearchTarget | None = None, limit: int = 5) -> Iterable[SearchResult]:
        results: list[SearchResult] = []

        if target in (None, "resource", "tool"):
            vector_hits = self.vector_store.search(query, limit=limit, item_type=target if target in ("resource", "tool") else None)
            for entity_id, score, hit_type in vector_hits:
                payload = self.resources.get(entity_id) if hit_type == "resource" else self.tools.get(entity_id)
                if payload:
                    results.append(SearchResult(id=entity_id, type=hit_type, score=score, payload=payload))

        if target in (None, "prompt"):
            lowered = query.lower()
            for prompt in self.prompts.list():
                if lowered in prompt.name.lower() or lowered in prompt.content.lower() or any(
                    lowered in tag.lower() for tag in prompt.tags
                ):
                    results.append(SearchResult(id=prompt.id, type="prompt", score=0.5, payload=prompt))

        return sorted(results, key=lambda r: r.score, reverse=True)[:limit]


